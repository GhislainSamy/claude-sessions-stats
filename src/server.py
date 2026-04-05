"""
UsageServer — serveur HTTP local qui reçoit les données de Tampermonkey
et les transmet au widget via un signal Qt.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from PySide6.QtCore import QObject, Signal

from usage_parser import parse_usage


class UsageServer(QObject):
    """Serveur HTTP localhost qui émet data_received à chaque POST /usage."""

    data_received = Signal(dict)

    def __init__(self, port: int, parent=None):
        super().__init__(parent)
        self._port = port
        self._server: HTTPServer | None = None

    def start(self) -> None:
        """Démarre le serveur HTTP dans un thread daemon."""
        signal_emitter = self  # référence pour le handler

        class _Handler(BaseHTTPRequestHandler):
            def do_OPTIONS(self):
                # Preflight CORS (certaines configs Tampermonkey l'envoient)
                self._send_cors()

            def do_POST(self):
                if self.path != "/usage":
                    self.send_response(404)
                    self.end_headers()
                    return

                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)

                try:
                    raw = json.loads(body)
                    interval_sec = int(raw.get("interval_sec", 0))
                    result = parse_usage(raw)
                    if result.get("ok"):
                        result["interval_sec"] = interval_sec
                except Exception:
                    result = {"ok": False, "error": "unknown"}

                # Émet le signal Qt (thread-safe — Qt queued connection)
                signal_emitter.data_received.emit(result)
                self._send_cors()

            def _send_cors(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *_):
                pass  # silence les logs HTTP dans la console

        self._server = HTTPServer(("localhost", self._port), _Handler)

        thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
