#!/usr/bin/env python3
import sys
import signal
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon


class HTMLViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Galago Tools Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set window icon with better path handling
        icon_path = os.path.join(os.path.dirname(__file__), "site_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon not found at: {icon_path}")
        
        # Create web view and set as central widget
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        
        # Load the HTML page
        self.web_view.setUrl(QUrl("http://localhost:8080"))


def main():
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    
    # Set application icon (this affects the taskbar icon on some systems)
    icon_path = os.path.join(os.path.dirname(__file__), "site_logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show the viewer
    viewer = HTMLViewer()
    viewer.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()