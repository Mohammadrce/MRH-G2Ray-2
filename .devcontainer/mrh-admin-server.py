#!/usr/bin/env python3
"""
MRH-G2Ray Admin Server
A secure HTTP server with Basic Authentication for serving the admin panel.
"""

import base64
import hmac
import logging
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Configuration
ADMIN_DIRECTORY = "/opt/mrh-admin"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Sample@Sample"
LISTEN_HOST = os.getenv("MRH_ADMIN_HOST", "0.0.0.0")
LISTEN_PORT = int(os.getenv("MRH_ADMIN_PORT", "8080"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _build_auth_token() -> str:
    """Build Base64-encoded auth token from environment variables or defaults."""
    username = os.getenv("MRH_ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    password = os.getenv("MRH_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    return base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")


def _validate_credentials(username: str, password: str) -> bool:
    """Validate credentials using timing-safe comparison."""
    expected_username = os.getenv("MRH_ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    expected_password = os.getenv("MRH_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    return hmac.compare_digest(username, expected_username) and hmac.compare_digest(
        password, expected_password
    )


class AdminAuthHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with Basic Authentication."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ADMIN_DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        """Override to use custom logger."""
        logger.info("%s - %s", self.address_string(), format % args)

    def log_error(self, format, *args):
        """Override to use custom logger."""
        logger.error("%s - %s", self.address_string(), format % args)

    def _get_credentials(self, authorization: str) -> tuple[str, str] | None:
        """Extract and decode credentials from Authorization header."""
        if not authorization.startswith("Basic "):
            return None
        try:
            token = authorization[6:].strip()
            decoded = base64.b64decode(token).decode("utf-8")
            if ":" not in decoded:
                return None
            username, password = decoded.split(":", 1)
            return username, password
        except (ValueError, UnicodeDecodeError):
            return None

    def _is_authorized(self) -> bool:
        """Check if the request is authorized."""
        authorization = self.headers.get("Authorization", "")
        credentials = self._get_credentials(authorization)
        if not credentials:
            return False
        username, password = credentials
        return _validate_credentials(username, password)

    def _request_auth(self):
        """Send 401 Unauthorized response."""
        self.send_response(401)
        self.send_header(
            "WWW-Authenticate", 'Basic realm="MRH Admin Panel", charset="UTF-8"'
        )
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", "27")
        self.end_headers()
        self.wfile.write(b"Authentication required.")

    def do_GET(self):
        """Handle GET requests with authentication."""
        if not self._is_authorized():
            self._request_auth()
            return
        super().do_GET()

    def do_HEAD(self):
        """Handle HEAD requests with authentication."""
        if not self._is_authorized():
            self._request_auth()
            return
        super().do_HEAD()

    def do_POST(self):
        """Handle POST requests with authentication."""
        if not self._is_authorized():
            self._request_auth()
            return
        self.send_response(405)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Method not allowed.")


def check_admin_directory() -> bool:
    """Check if admin directory exists and contains index.html."""
    admin_path = Path(ADMIN_DIRECTORY)
    if not admin_path.exists():
        logger.error(f"Admin directory does not exist: {ADMIN_DIRECTORY}")
        return False
    if not (admin_path / "index.html").exists():
        logger.error(f"index.html not found in {ADMIN_DIRECTORY}")
        return False
    return True


if __name__ == "__main__":
    # Security warning
    username = os.getenv("MRH_ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    password = os.getenv("MRH_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    if username == DEFAULT_ADMIN_USERNAME or password == DEFAULT_ADMIN_PASSWORD:
        logger.warning(
            "WARNING: Default admin credential detected. "
            "Set MRH_ADMIN_USERNAME and MRH_ADMIN_PASSWORD environment variables to override."
        )

    # Validate admin directory
    if not check_admin_directory():
        sys.exit(1)

    # Start server
    try:
        server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), AdminAuthHandler)
        logger.info(
            f"Starting MRH Admin Server on {LISTEN_HOST}:{LISTEN_PORT}"
        )
        server.serve_forever()
    except OSError as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        server.shutdown()
