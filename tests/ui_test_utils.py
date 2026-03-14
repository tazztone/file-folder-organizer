from unittest.mock import MagicMock


class MockBase(object):
    def __init__(self, *args, **kwargs):
        self._config = {}
        self.setObjectName = MagicMock()
        self.setStyleSheet = MagicMock()
        self.setFixedSize = MagicMock()
        self.setFixedHeight = MagicMock()
        self.setFixedWidth = MagicMock()
        self.setAlignment = MagicMock()
        self.setContentsMargins = MagicMock()
        self.setSpacing = MagicMock()
        self.addWidget = MagicMock()
        self.addLayout = MagicMock()
        self.addStretch = MagicMock()
        self.insertWidget = MagicMock()
        self.setText = MagicMock()
        self.text = MagicMock(return_value="")
        self.value = MagicMock(return_value=0)
        self.setValue = MagicMock()
        self.setRange = MagicMock()
        self.show = MagicMock()
        self.hide = MagicMock()
        self.setEnabled = MagicMock()
        self.clicked = MagicMock()
        self.clicked.connect = MagicMock()
        self.stateChanged = MagicMock()
        self.stateChanged.connect = MagicMock()
        self.currentTextChanged = MagicMock()
        self.currentTextChanged.connect = MagicMock()
        self.valueChanged = MagicMock()
        self.valueChanged.connect = MagicMock()
        self.dropped = MagicMock()
        self.dropped.connect = MagicMock()
        self.setAcceptDrops = MagicMock()
        self.setCursor = MagicMock()
        self.update = MagicMock()
        self.rect = MagicMock(return_value=MagicMock())
        self.rect().adjusted = MagicMock(return_value=MagicMock())
        self.deleteLater = MagicMock()
        self.count = MagicMock(return_value=0)
        self.takeAt = MagicMock()
        self.layout = MagicMock()
        self.addItem = MagicMock()
        self.addItems = MagicMock()
        self.clear = MagicMock()
        self.setCurrentText = MagicMock()
        self.blockSignals = MagicMock()
        self.setToolTip = MagicMock()
        self.exec = MagicMock(return_value=1)
        self.accept = MagicMock()
        self.reject = MagicMock()
        self.setReadOnly = MagicMock()
        self.append = MagicMock()
        self.setPlainText = MagicMock()
        self.toPlainText = MagicMock(return_value="")
        self.setChecked = MagicMock()
        self.isChecked = MagicMock(return_value=False)
        self.setWindowTitle = MagicMock()
        self.resize = MagicMock()
        self.setCentralWidget = MagicMock()
        self.connect = MagicMock()
        self.emit = MagicMock()

        self.style = MagicMock()
        self._mock_style_obj = MagicMock()
        self._mock_style_obj.unpolish = MagicMock()
        self._mock_style_obj.polish = MagicMock()
        self.style.return_value = self._mock_style_obj

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name):
        # Fallback for signals like stateChanged, etc.
        if name in [
            "stateChanged",
            "clicked",
            "currentTextChanged",
            "valueChanged",
            "dropped",
            "finished",
            "status_updated",
            "progress_updated",
            "log_emitted",
        ]:
            sig = MagicMock()
            sig.connect = MagicMock()
            sig.emit = MagicMock()
            setattr(self, name, sig)
            return sig

        # Auto-mock layout/widget helper methods
        if name.startswith("add") or name.startswith("set") or name.startswith("insert"):
            m = MagicMock()
            setattr(self, name, m)
            return m

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class MockModule(object):
    pass


def get_pyside_mocks():
    mock_qtwidgets = MockModule()

    class MockQApplication(MockBase):
        @staticmethod
        def instance():
            return mock_app_instance

        @staticmethod
        def palette():
            return mock_palette

    mock_app_instance = MockBase()
    mock_palette = MagicMock()
    mock_color = MagicMock()
    mock_color.lightness.return_value = 100  # Dark by default
    mock_palette.color.return_value = mock_color

    mock_qtwidgets.QApplication = MockQApplication
    mock_qtwidgets.QMainWindow = MockBase
    mock_qtwidgets.QWidget = MockBase
    mock_qtwidgets.QFrame = MockBase
    mock_qtwidgets.QVBoxLayout = MockBase
    mock_qtwidgets.QHBoxLayout = MockBase
    mock_qtwidgets.QGridLayout = MockBase
    mock_qtwidgets.QSizePolicy = MockModule()
    mock_qtwidgets.QSizePolicy.Policy = MockModule()
    mock_qtwidgets.QSizePolicy.Policy.Fixed = 1

    def mock_qlabel(text="", parent=None):
        m = MockBase(parent)
        m.text.return_value = text
        return m

    mock_qtwidgets.QLabel = MagicMock(side_effect=mock_qlabel)
    mock_qtwidgets.QPushButton = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_qtwidgets.QCheckBox = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_qtwidgets.QComboBox = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_qtwidgets.QSlider = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_qtwidgets.QProgressBar = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_qtwidgets.QScrollArea = MagicMock(side_effect=lambda *args, **kwargs: MockBase(*args, **kwargs))
    mock_qtwidgets.QFileDialog = MagicMock()
    mock_qtwidgets.QFileDialog.getExistingDirectory = MagicMock(return_value="/mock/path")
    mock_qtwidgets.QFileDialog.getSaveFileName = MagicMock(return_value=("/mock/file.json", "filter"))
    mock_qtwidgets.QFileDialog.getOpenFileName = MagicMock(return_value=("/mock/file.json", "filter"))
    mock_qtwidgets.QMessageBox = MockModule()
    mock_qtwidgets.QMessageBox.Yes = 1
    mock_qtwidgets.QMessageBox.No = 0
    mock_qtwidgets.QMessageBox.StandardButton = MockModule()
    mock_qtwidgets.QMessageBox.StandardButton.Yes = 1
    mock_qtwidgets.QMessageBox.StandardButton.No = 0
    mock_qtwidgets.QMessageBox.question = MagicMock(return_value=1)
    mock_qtwidgets.QMessageBox.information = MagicMock()
    mock_qtwidgets.QMessageBox.critical = MagicMock()
    mock_qtwidgets.QMessageBox.warning = MagicMock()
    mock_qtwidgets.QDialog = MockBase
    mock_qtwidgets.QTabWidget = MockBase
    mock_qtwidgets.QTextEdit = MockBase
    mock_qtwidgets.QPlainTextEdit = MockBase
    mock_qtwidgets.QLineEdit = MockBase
    mock_qtwidgets.QAbstractButton = MockBase
    mock_qtwidgets.QInputDialog = MagicMock()
    mock_qtwidgets.QInputDialog.getText = MagicMock(return_value=("mock_text", True))

    mock_qtcore = MockModule()
    mock_qtcore.Qt = MockModule()
    mock_qtcore.Qt.AlignmentFlag = MockModule()
    mock_qtcore.Qt.AlignmentFlag.AlignCenter = 1
    mock_qtcore.Qt.CursorShape = MockModule()
    mock_qtcore.Qt.CursorShape.PointingHandCursor = 1
    mock_qtcore.Qt.Orientation = MockModule()
    mock_qtcore.Qt.Orientation.Horizontal = 1
    mock_qtcore.Qt.CheckState = MockModule()
    mock_qtcore.Qt.CheckState.Checked = 2
    mock_qtcore.Qt.WidgetAttribute = MockModule()
    mock_qtcore.Qt.WidgetAttribute.WA_StyledBackground = 1
    mock_qtcore.Qt.MouseButton = MockModule()
    mock_qtcore.Qt.MouseButton.LeftButton = 1
    mock_qtcore.Qt.GlobalColor = MockModule()
    mock_qtcore.Qt.GlobalColor.white = 1
    mock_qtcore.Qt.PenStyle = MockModule()
    mock_qtcore.Qt.PenStyle.NoPen = 0
    mock_qtcore.Qt.PenStyle.DashLine = 1

    mock_qtcore.Qt.AlignCenter = 1
    mock_qtcore.Qt.Horizontal = 1
    mock_qtcore.Qt.Checked = 2
    mock_qtcore.Qt.Unchecked = 0
    mock_qtcore.Qt.LeftButton = 1
    mock_qtcore.Qt.PointingHandCursor = 1
    mock_qtcore.Qt.DashLine = 1
    mock_qtcore.QTimer = MagicMock()
    def mock_single_shot(*args):
        # QTimer.singleShot(ms, slot) or QTimer.singleShot(ms, receiver, slot)
        if len(args) == 2:
            args[1]()
        elif len(args) == 3:
            args[2]()

    mock_qtcore.QTimer.singleShot = MagicMock(side_effect=mock_single_shot)
    mock_qtcore.Signal = MagicMock(side_effect=lambda *args: MagicMock())
    mock_qtcore.QObject = MockBase
    mock_qtcore.QSize = MagicMock()
    mock_qtcore.QPoint = MagicMock()
    mock_qtcore.QPropertyAnimation = lambda *args, **kwargs: MagicMock()
    mock_qtcore.QEasingCurve = MockModule()
    mock_qtcore.QEasingCurve.Type = MockModule()
    mock_qtcore.QEasingCurve.Type.InOutExpo = 1
    mock_qtcore.QEasingCurve.InOutExpo = 1
    mock_qtcore.Property = MagicMock

    mock_qtgui = MockModule()
    mock_qtgui.QPainter = MagicMock()
    mock_qtgui.QPainter.RenderHint = MockModule()
    mock_qtgui.QPainter.RenderHint.Antialiasing = 1
    mock_qtgui.QPen = MagicMock()
    mock_qtgui.QColor = MagicMock()
    mock_qtgui.QFont = MagicMock()
    mock_qtgui.QIcon = MagicMock()
    mock_qtgui.QDragEnterEvent = MagicMock()
    mock_qtgui.QDropEvent = MagicMock()
    mock_qtgui.QPalette = MockModule()
    mock_qtgui.QPalette.ColorRole = MockModule()
    mock_qtgui.QPalette.ColorRole.Window = 1
    mock_qtgui.QPalette.Window = 1
    mock_qtgui.QBrush = MagicMock

    return mock_qtwidgets, mock_qtcore, mock_qtgui
