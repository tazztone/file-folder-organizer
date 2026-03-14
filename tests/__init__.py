import logging

# Global test setup: silence all application logging during tests
# to prevent confusing output from tests that check error-handling paths.
logging.disable(logging.CRITICAL)
