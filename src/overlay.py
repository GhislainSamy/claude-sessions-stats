"""
CCOverlayWindow — widget overlay ultra-compact.
[timer] [logo] ⚡ session · 🗓️ hebdo · drag partout · clic droit pour options.
"""

from __future__ import annotations

import configparser
import os
import sys

import styles as _styles_mod
from PySide6.QtCore import QPoint, QPropertyAnimation, QTimer, Qt, Slot
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from server import UsageServer
from styles import LOGO_SIZE, PCT_WIDTH, RESET_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH


def _logo_path() -> str:
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, "claude_logo.png")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "claude_logo.png")


class CCOverlayWindow(QWidget):

    def __init__(self, server: UsageServer, *, show_timer: bool = True,
                 config_path: str = "config.ini",
                 anim_pulse: bool = True, anim_blink: bool = True,
                 locked: bool = False):
        super().__init__()
        self._drag_pos: QPoint | None = None
        self._elapsed_seconds: int = 0
        self._show_timer = show_timer
        self._config_path = config_path
        self._anim_pulse = anim_pulse
        self._anim_blink = anim_blink
        self._locked = locked
        self._prev_session: int | None = None
        self._prev_weekly: int | None = None
        self._pulse_anim: QPropertyAnimation | None = None
        self._blink_timer: QTimer | None = None
        self._current_size = next(
            (k for k, v in _styles_mod._SIZES.items() if v[1] == _styles_mod.WINDOW_HEIGHT),
            "compact",
        )

        self._setup_window()
        self._build_ui()

        server.data_received.connect(self._on_stats_updated)

        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1_000)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start()

    # ── Setup ──────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(6, 4, 6, 4)
        root.setSpacing(6)

        # ── Timer (à gauche du logo) ──
        self._timer_label = QLabel("--:--")
        self._timer_label.setObjectName("timer_label")
        self._timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._interval_label = QLabel("")
        self._interval_label.setObjectName("interval_label")
        self._interval_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        timer_box = QVBoxLayout()
        timer_box.setSpacing(0)
        timer_box.setContentsMargins(0, 0, 0, 0)
        timer_box.addWidget(self._timer_label)
        timer_box.addWidget(self._interval_label)

        self._timer_widget = QWidget()
        self._timer_widget.setLayout(timer_box)
        self._timer_widget.setFixedWidth(_styles_mod._SIZES[self._current_size][9])
        self._timer_widget.setVisible(self._show_timer)
        root.addWidget(self._timer_widget)

        # ── Logo ──
        self._logo_label = QLabel()
        pixmap = QPixmap(_logo_path())
        if not pixmap.isNull():
            self._logo_label.setPixmap(
                pixmap.scaled(LOGO_SIZE, LOGO_SIZE,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )
        self._logo_label.setFixedSize(LOGO_SIZE, LOGO_SIZE)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._logo_label)

        # ── Contenu (2 lignes) ──
        content = QVBoxLayout()
        content.setSpacing(3)
        content.addLayout(self._make_row("⚡", "session"))
        content.addLayout(self._make_row("🗓️", "weekly"))
        root.addLayout(content)

        # ── Cadenas (overlay flottant, hors layout) ──
        self._lock_btn = QLabel("🔒" if self._locked else "🔓", self)
        self._lock_btn.setObjectName("lock_btn")
        self._lock_btn.setFixedSize(10, 10)
        self._lock_btn.setStyleSheet("font-size: 8px;")
        self._lock_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lock_btn.move(3, 3)
        self._lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lock_btn.raise_()

    def _make_row(self, emoji: str, prefix: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(3)

        emoji_lbl = QLabel(emoji)
        emoji_lbl.setObjectName("emoji_label")
        emoji_lbl.setFixedWidth(18)
        row.addWidget(emoji_lbl)
        setattr(self, f"_{prefix}_emoji", emoji_lbl)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row.addWidget(bar)

        pct = QLabel("--")
        pct.setObjectName("pct_label")
        pct.setFixedWidth(PCT_WIDTH)
        pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(pct)

        reset = QLabel("…")
        reset.setObjectName("reset_label")
        reset.setFixedWidth(RESET_WIDTH)
        row.addWidget(reset)

        setattr(self, f"_{prefix}_bar",   bar)
        setattr(self, f"_{prefix}_pct",   pct)
        setattr(self, f"_{prefix}_reset", reset)

        return row

    # ── Stay on top ────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._force_os_topmost()

    def _force_os_topmost(self) -> None:
        if sys.platform == "win32":
            try:
                import ctypes
                HWND_TOPMOST = -1
                SWP_NOMOVE   = 0x0002
                SWP_NOSIZE   = 0x0001
                ctypes.windll.user32.SetWindowPos(
                    int(self.winId()), HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE,
                )
            except Exception:
                pass

    # ── Timer ──────────────────────────────────────────────────────

    def _tick(self) -> None:
        self._elapsed_seconds += 1
        m, s = divmod(self._elapsed_seconds, 60)
        self._timer_label.setText(f"{m:02d}:{s:02d}")

    # ── Données ────────────────────────────────────────────────────

    @Slot(dict)
    def _on_stats_updated(self, data: dict) -> None:
        if not data.get("ok"):
            self._show_error(data.get("error", "unknown"))
            return

        self._elapsed_seconds = 0
        self._timer_label.setText("00:00")

        interval = data.get("interval_sec", 0)
        self._interval_label.setText(f"/{interval}s" if interval > 0 else "")

        for prefix in ("session", "weekly"):
            new_val = data[prefix]["value"]
            prev = getattr(self, f"_prev_{prefix}")
            if prev is not None and prev > 10 and new_val <= 5:
                self._on_reset_detected(prefix)
            setattr(self, f"_prev_{prefix}", new_val)

        self._update_row(self._session_bar, self._session_pct, self._session_reset, data["session"])
        self._update_row(self._weekly_bar,  self._weekly_pct,  self._weekly_reset,  data["weekly"])

    def _update_row(self, bar: QProgressBar, pct: QLabel, reset: QLabel, data: dict) -> None:
        value = data["value"]
        bar.setValue(value)
        pct.setText(f"{value}%")

        bar.setProperty("usage", "high" if value >= 80 else "normal")
        bar.style().unpolish(bar)
        bar.style().polish(bar)

        reset.setObjectName("reset_label")
        reset.style().unpolish(reset)
        reset.style().polish(reset)
        reset.setText(data["label"])

    def _show_error(self, error: str) -> None:
        msgs = {
            "network_error": "hors ligne",
            "rate_limited":  "429",
            "unknown":       "erreur",
        }
        self._session_reset.setText(msgs.get(error, error))
        self._session_reset.setObjectName("error_label")
        self._session_reset.style().unpolish(self._session_reset)
        self._session_reset.style().polish(self._session_reset)

    # ── Animations au reset ────────────────────────────────────────

    def _on_reset_detected(self, prefix: str) -> None:
        if self._anim_pulse:
            self._start_pulse_anim()
        if self._anim_blink:
            self._start_blink_anim(prefix)

    def _start_pulse_anim(self) -> None:
        if self._pulse_anim and self._pulse_anim.state() == QPropertyAnimation.State.Running:
            self._pulse_anim.stop()
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(1200)
        anim.setLoopCount(5)
        anim.setKeyValueAt(0,   1.0)
        anim.setKeyValueAt(0.5, 0.25)
        anim.setKeyValueAt(1.0, 1.0)
        anim.finished.connect(lambda: self.setWindowOpacity(self.windowOpacity()))
        anim.start()
        self._pulse_anim = anim

    def _start_blink_anim(self, prefix: str) -> None:
        if self._blink_timer and self._blink_timer.isActive():
            self._blink_timer.stop()
        emoji_lbl = getattr(self, f"_{prefix}_emoji")
        count = [0]

        def _toggle() -> None:
            count[0] += 1
            emoji_lbl.setVisible(count[0] % 2 == 0)
            if count[0] >= 16:
                timer.stop()
                emoji_lbl.setVisible(True)

        timer = QTimer(self)
        timer.setInterval(250)
        timer.timeout.connect(_toggle)
        timer.start()
        self._blink_timer = timer

    # ── Menu contextuel ────────────────────────────────────────────

    def contextMenuEvent(self, event) -> None:
        from PySide6.QtWidgets import QApplication
        menu = QMenu(self)

        size_menu = menu.addMenu("Taille")
        for label, key in [("Compact", "compact"), ("Moyen", "medium"), ("Grand", "large")]:
            a = size_menu.addAction(label)
            a.setCheckable(True)
            a.setChecked(key == self._current_size)
            a.triggered.connect(lambda checked, k=key: self._change_size(k))

        timer_action = menu.addAction("Afficher le timer")
        timer_action.setCheckable(True)
        timer_action.setChecked(self._show_timer)
        timer_action.triggered.connect(self._toggle_timer)

        anim_menu = menu.addMenu("Animations au reset")
        pulse_action = anim_menu.addAction("Pulsation fenêtre")
        pulse_action.setCheckable(True)
        pulse_action.setChecked(self._anim_pulse)
        pulse_action.triggered.connect(lambda checked: self._toggle_anim("anim_pulse", checked))

        blink_action = anim_menu.addAction("Clignotement emoji")
        blink_action.setCheckable(True)
        blink_action.setChecked(self._anim_blink)
        blink_action.triggered.connect(lambda checked: self._toggle_anim("anim_blink", checked))

        # ── Slider transparence intégré au menu ──
        opacity_widget = QWidget()
        opacity_layout = QHBoxLayout(opacity_widget)
        opacity_layout.setContentsMargins(16, 4, 8, 4)
        opacity_layout.setSpacing(6)
        opacity_layout.addWidget(QLabel("🌫️"))
        opacity_slider = QSlider(Qt.Orientation.Horizontal)
        opacity_slider.setRange(20, 100)
        opacity_slider.setValue(int(self.windowOpacity() * 100))
        opacity_slider.setFixedWidth(110)
        opacity_pct = QLabel(f"{opacity_slider.value()}%")
        opacity_pct.setFixedWidth(36)
        opacity_layout.addWidget(opacity_slider)
        opacity_layout.addWidget(opacity_pct)

        opacity_slider.valueChanged.connect(
            lambda v: (opacity_pct.setText(f"{v}%"), self.setWindowOpacity(v / 100))
        )
        opacity_slider.sliderReleased.connect(
            lambda: self._save_config("opacity", str(opacity_slider.value()))
        )

        wa = QWidgetAction(menu)
        wa.setDefaultWidget(opacity_widget)
        menu.addAction(wa)
        menu.addSeparator()
        menu.addAction("Quitter").triggered.connect(QApplication.quit)
        menu.exec(event.globalPos())

    # ── Actions menu ───────────────────────────────────────────────

    def _change_size(self, name: str) -> None:
        from PySide6.QtWidgets import QApplication
        _styles_mod.apply_size(name)
        self._current_size = name

        self.setFixedSize(_styles_mod.WINDOW_WIDTH, _styles_mod.WINDOW_HEIGHT)

        pixmap = QPixmap(_logo_path())
        if not pixmap.isNull():
            self._logo_label.setPixmap(
                pixmap.scaled(_styles_mod.LOGO_SIZE, _styles_mod.LOGO_SIZE,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )
        self._logo_label.setFixedSize(_styles_mod.LOGO_SIZE, _styles_mod.LOGO_SIZE)

        self._timer_widget.setFixedWidth(_styles_mod._SIZES[name][9])
        for lbl in (self._session_pct, self._weekly_pct):
            lbl.setFixedWidth(_styles_mod.PCT_WIDTH)
        for lbl in (self._session_reset, self._weekly_reset):
            lbl.setFixedWidth(_styles_mod.RESET_WIDTH)

        QApplication.instance().setStyleSheet(_styles_mod.STYLESHEET)
        self._save_config("size", name)

    def _toggle_timer(self) -> None:
        self._show_timer = not self._show_timer
        self._timer_widget.setVisible(self._show_timer)
        self._save_config("show_timer", "true" if self._show_timer else "false")

    def _toggle_anim(self, key: str, value: bool) -> None:
        setattr(self, f"_{key}", value)
        self._save_config(key, "true" if value else "false")

    def _toggle_lock(self) -> None:
        self._locked = not self._locked
        self._lock_btn.setText("🔒" if self._locked else "🔓")
        self._save_config("locked", "true" if self._locked else "false")

    def _save_config(self, key: str, value: str) -> None:
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(self._config_path, encoding="utf-8")
        if "app" not in cfg:
            cfg["app"] = {}
        cfg["app"][key] = value
        with open(self._config_path, "w", encoding="utf-8") as f:
            cfg.write(f)

    # ── Clamp position ─────────────────────────────────────────────

    def _clamp_to_screen(self, pos: QPoint, size=None) -> QPoint:
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w = size.width()  if size else self.width()
        h = size.height() if size else self.height()
        x = max(screen.left(), min(pos.x(), screen.right()  - w))
        y = max(screen.top(),  min(pos.y(), screen.bottom() - h))
        return QPoint(x, y)

    # ── Drag & Drop ────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._lock_btn.geometry().contains(event.pos()):
                self._toggle_lock()
                event.accept()
                return
            if not self._locked:
                self._drag_pos = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(self._clamp_to_screen(new_pos))
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None

    # ── Fond transparent ───────────────────────────────────────────

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(15, 20, 35, 225))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
