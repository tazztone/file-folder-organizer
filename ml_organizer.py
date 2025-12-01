import os
import torch
import shutil
import numpy as np
from pathlib import Path
from PIL import Image

# Import only when needed to save startup time, but since this module is imported
# when "Smart Categorization" is enabled, top-level imports are acceptable if they are used throughout.
# However, to be safe with startup time if this module is imported early, we might defer some.
# But for now, standard imports.

try:
    from transformers import AutoModel, AutoProcessor, AutoTokenizer
    from sentence_transformers import SentenceTransformer
    import pypdf
    import docx
except ImportError:
    # This should be handled by requirements.txt, but safe guard
    pass

class MultimodalFileOrganizer:
    def __init__(self, categories_config=None):
        self.device = self._get_device()
        self.categories_config = categories_config or {}
        self.text_model = None
        self.image_model = None
        self.image_processor = None
        self.text_category_embeddings = {}

        # Flags
        self.models_loaded = False

    def _get_device(self):
        """Detects the best available device (CUDA, MPS, or CPU)."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def are_models_present(self):
        """
        Checks if the models are likely present in the cache.
        """
        try:
            from transformers import AutoConfig
            # Check SigLIP
            AutoConfig.from_pretrained("google/siglip2-base-patch32-256", local_files_only=True)
            # Check Qwen - SentenceTransformer stores in ~/.cache/torch/sentence_transformers usually
            # We can try to load just the configuration/modules.json lightly or rely on SigLIP as proxy
            return True
        except Exception:
            return False

    def ensure_models(self, progress_callback=None):
        """
        Downloads models if missing, but does not load them into VRAM unless necessary.
        Actually, for this library, downloading usually happens during load.
        So this is an alias for load_models but semantically used for 'Download' button.
        """
        self.load_models(progress_callback)

    def load_models(self, progress_callback=None):
        """
        Loads the models. Downloads them if not present.
        """
        if self.models_loaded:
            if progress_callback:
                progress_callback("Models already loaded.", 1.0)
            return

        try:
            if progress_callback:
                progress_callback("Loading Text Model (Qwen)...", 0.1)

            # Load Text Model
            self.text_model = SentenceTransformer(
                "Qwen/Qwen3-Embedding-0.6B",
                device=self.device,
                trust_remote_code=True
            )

            if progress_callback:
                progress_callback("Loading Image Model (SigLIP)...", 0.4)

            # Load Image Model
            self.image_model = AutoModel.from_pretrained(
                "google/siglip2-base-patch32-256",
            ).to(self.device).eval()

            self.image_processor = AutoProcessor.from_pretrained(
                "google/siglip2-base-patch32-256"
            )

            if progress_callback:
                progress_callback("Precomputing embeddings...", 0.8)

            self._precompute_text_embeddings()

            if progress_callback:
                progress_callback("Models loaded.", 1.0)

            self.models_loaded = True

        except Exception as e:
            print(f"Error loading ML models: {e}")
            raise e

    def _precompute_text_embeddings(self):
        """Precompute category embeddings for text"""
        self.text_category_embeddings = {}
        instruction = "Instruct: Classify this content into file categories\nQuery:"

        if not self.categories_config:
            return

        for cat, desc in self.categories_config.items():
            if "text" in desc:
                text_to_encode = f"{instruction}{desc['text']}"
                emb = self.text_model.encode(
                    text_to_encode,
                    prompt_name="query",
                    convert_to_numpy=True
                )
                self.text_category_embeddings[cat] = emb

    def extract_text(self, file_path: Path):
        """Extracts text from various file formats."""
        ext = file_path.suffix.lower()
        content = ""

        try:
            if ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(5000) # Limit to first 5KB

            elif ext == '.pdf':
                try:
                    reader = pypdf.PdfReader(file_path)
                    # Extract text from first few pages
                    for i in range(min(3, len(reader.pages))):
                        page_text = reader.pages[i].extract_text()
                        if page_text:
                            content += page_text + "\n"
                except Exception as e:
                    print(f"PDF extraction error: {e}")

            elif ext == '.docx':
                try:
                    doc = docx.Document(file_path)
                    # Limit paragraphs
                    paragraphs = [p.text for p in doc.paragraphs[:50]]
                    content = "\n".join(paragraphs)
                except Exception as e:
                    print(f"Docx extraction error: {e}")

        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")

        return content

    def categorize_image(self, image_path):
        """Categorize image using SigLIP 2"""
        if not self.models_loaded:
            return None, 0.0

        try:
            image = Image.open(image_path).convert("RGB")

            # Collect all visual descriptions
            all_labels = []
            label_to_category = {}

            for cat, desc in self.categories_config.items():
                if 'visual' in desc:
                    # 'visual' can be a list or a string. Handle both.
                    visual_descs = desc['visual']
                    if isinstance(visual_descs, str):
                        visual_descs = [visual_descs]

                    for label in visual_descs:
                        all_labels.append(label)
                        label_to_category[label] = cat

            if not all_labels:
                return None, 0.0

            # Prepare inputs
            inputs = self.image_processor(
                images=image,
                text=all_labels,
                return_tensors="pt",
                padding="max_length"
            ).to(self.device)

            # Get predictions
            with torch.no_grad():
                outputs = self.image_model(**inputs)
                # SigLIP uses sigmoid instead of softmax
                probs = torch.sigmoid(outputs.logits_per_image[0])

            # Find best match
            best_idx = probs.argmax().item()
            best_label = all_labels[best_idx]
            confidence = probs[best_idx].item()
            category = label_to_category[best_label]

            return category, confidence

        except Exception as e:
            print(f"Error categorizing image {image_path}: {e}")
            return None, 0.0

    def categorize_text_file(self, file_path, content, threshold=0.4):
        """Categorize text-based file using Qwen3"""
        if not self.models_loaded or not content or len(content.strip()) < 10:
            return None, 0.0

        try:
            instruction = "Instruct: Classify this content into file categories\nQuery:"
            # Qwen embedding
            content_emb = self.text_model.encode(
                f"{instruction}{content[:2000]}",
                prompt_name="query",
                convert_to_numpy=True
            )

            # Compute similarities
            similarities = {}
            for cat, cat_emb in self.text_category_embeddings.items():
                # Cosine similarity
                sim = np.dot(content_emb, cat_emb) / (
                    np.linalg.norm(content_emb) * np.linalg.norm(cat_emb) + 1e-9
                )
                similarities[cat] = sim

            if not similarities:
                return None, 0.0

            best_category = max(similarities.items(), key=lambda x: x[1])
            return best_category[0], float(best_category[1])

        except Exception as e:
            print(f"Error categorizing text {file_path}: {e}")
            return None, 0.0

    def smart_categorize(self, file_path, threshold=0.3):
        """Main categorization method"""
        if not self.models_loaded:
            return None, 0.0, "ml-not-loaded"

        file_ext = file_path.suffix.lower()

        # Image files
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            category, confidence = self.categorize_image(file_path)
            if confidence > threshold:  # Threshold for trusting ML (SigLIP is usually confident)
                return category, confidence, "image-ml"

        # Text-extractable files
        elif file_ext in ['.txt', '.md', '.py', '.js', '.html', '.pdf', '.docx', '.css', '.json']:
            content = self.extract_text(file_path)
            if content:
                # Use slightly higher threshold for text if needed, or same
                category, confidence = self.categorize_text_file(file_path, content)
                if confidence > threshold: # Qwen threshold
                    return category, confidence, "text-ml"

        return None, 0.0, "extension"
