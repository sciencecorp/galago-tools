import sys
import signal
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer, Qt
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class GalagoWebViewer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Galago Tools Manager")
        self.setGeometry(100, 100, 1000, 800)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "site_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon not found at: {icon_path}")
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        # Create web view
        self.web_view = QWebEngineView()
        self.main_layout.addWidget(self.web_view)
        
        # Create error widget (initially hidden)
        self.create_error_widget()
        
        # Network manager for checking server availability
        self.network_manager = QNetworkAccessManager()
        
        # Timer for retrying connection
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self.check_server_and_load)
        
        # Initial load attempt
        self.check_server_and_load()
    
    def create_error_widget(self) -> None:
        """Create the error display widget"""
        self.error_widget = QWidget()
        error_layout = QVBoxLayout(self.error_widget)
        
        # Error message
        self.error_label = QLabel()
        self.error_label.setText(
            "<div style='text-align: center; padding: 50px;'>"
            "<h2 style='color: #666; margin-bottom: 20px;'>🔌 Connection Error</h2>"
            "<p style='font-size: 16px; color: #888; margin-bottom: 30px;'>"
            "Unable to connect to the Galago Tools server at localhost:8080</p>"
            "<p style='color: #999;'>Please make sure the server is running and try again.</p>"
            "</div>"
        )
        self.error_label.setWordWrap(True)
        error_layout.addWidget(self.error_label)
        
        # Retry button
        self.retry_button = QPushButton("Retry Connection")
        self.retry_button.setMaximumWidth(200)
        self.retry_button.clicked.connect(self.check_server_and_load)
        error_layout.addWidget(self.retry_button, Qt.AlignmentFlag.AlignCenter)
        
        # Add error widget to layout but hide it initially
        self.main_layout.addWidget(self.error_widget)
        self.error_widget.hide()

    def check_server_and_load(self) -> None:
        """Check if server is reachable before loading the page"""
        self.retry_button.setText("Checking connection...")
        self.retry_button.setEnabled(False)
        
        # Create a simple GET request to check server availability
        request = QNetworkRequest(QUrl("http://localhost:8080"))
        request.setRawHeader(b"User-Agent", b"Galago-Checker")
        
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handle_server_check(reply))

    def handle_server_check(self, reply: QNetworkReply) -> None:
        """Handle the server check response"""
        self.retry_button.setText("Retry Connection")
        self.retry_button.setEnabled(True)
        
        if reply.error() == QNetworkReply.NetworkError.NoError:
            # Server is reachable, show web view and load page
            self.show_web_view()
            self.web_view.setUrl(QUrl("http://localhost:8080"))
        else:
            # Server is not reachable, show error message
            self.show_error_message()
            # Auto-retry after 5 seconds
            self.retry_timer.start(5000)
        
        reply.deleteLater()
    
    def show_web_view(self) -> None:
        """Show the web view and hide error message"""
        self.retry_timer.stop()  # Stop auto-retry timer
        self.web_view.show()
        self.error_widget.hide()
    
    def show_error_message(self) -> None:
        """Show error message and hide web view"""
        self.web_view.hide()
        self.error_widget.show()


def main() -> None:
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(__file__), "site_logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show the viewer
    viewer = GalagoWebViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()