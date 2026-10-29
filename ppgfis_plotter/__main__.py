from .common import QApplication, QFont, UI_FONT, sys
from .window import MainWindow

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setFont(QFont(UI_FONT, 10))
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
