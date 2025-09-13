import sys
from PySide6.QtWidgets import QApplication
from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("FlowDraw")
    app.setOrganizationName("FlowDraw")
    window = MainWindow()
    window.show()
    if len(sys.argv) > 1:
        window.open_file(sys.argv[1])
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
