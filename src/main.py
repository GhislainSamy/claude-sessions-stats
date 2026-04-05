"""
Claude Session Stats — Point d'entrée.
Lance le serveur HTTP local puis l'overlay PySide6.
"""

from __future__ import annotations

import configparser
import logging
import os
import sys

# ── Logging global ────────────────────────────────────────────────
logging.basicConfig(
    filename=os.path.join(
        os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__),
        "claude_stats_error.log",
    ),
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)


def _excepthook(exc_type, exc_value, exc_tb):
    logging.error("Exception non gérée", exc_info=(exc_type, exc_value, exc_tb))
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = _excepthook


# ── Config ────────────────────────────────────────────────────────

def _get_config_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        # Dev : config.ini est à la racine du projet, un niveau au-dessus de src/
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "config.ini")


def _load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser(interpolation=None)
    path = _get_config_path()

    if not os.path.exists(path):
        config["server"] = {"port": "7842"}
        config["app"] = {"start_position_x": "100", "start_position_y": "100"}
        with open(path, "w", encoding="utf-8") as f:
            config.write(f)

    config.read(path, encoding="utf-8")
    return config


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    config = _load_config()

    port  = config.getint("server", "port",            fallback=7842)
    pos_x = config.getint("app",    "start_position_x", fallback=100)
    pos_y = config.getint("app",    "start_position_y", fallback=100)
    size       = config.get       ("app", "size",       fallback="compact")
    show_timer = config.getboolean("app", "show_timer", fallback=True)
    anim_pulse = config.getboolean("app", "anim_pulse", fallback=True)
    anim_blink = config.getboolean("app", "anim_blink", fallback=True)

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    import styles
    styles.apply_size(size)
    from overlay import CCOverlayWindow
    from server import UsageServer
    from styles import STYLESHEET

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Claude Session Stats")
    app.setApplicationVersion("1.0.0")
    app.setQuitOnLastWindowClosed(True)
    app.setStyleSheet(STYLESHEET)

    server = UsageServer(port)
    server.start()

    window = CCOverlayWindow(server, show_timer=show_timer, config_path=_get_config_path(),
                             anim_pulse=anim_pulse, anim_blink=anim_blink)
    window.move(pos_x, pos_y)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
