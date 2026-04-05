"""
Constantes visuelles et QSS stylesheet — taille pilotée par config.ini.
"""

# (width, height, logo, t_base, t_emoji, t_pct, t_reset, t_timer, bar_h, timer_w, pct_w, reset_w)
_SIZES = {
    "compact": (370, 47, 32, 10, 12, 10,  9, 10, 4, 34, 32, 52),
    "medium":  (370, 60, 38, 12, 14, 12, 11, 12, 5, 40, 38, 62),
    "large":   (370, 76, 46, 14, 16, 14, 13, 14, 6, 48, 44, 72),
}

WINDOW_WIDTH  = 400
WINDOW_HEIGHT = 47
LOGO_SIZE     = 32
STYLESHEET    = ""
PCT_WIDTH     = 32
RESET_WIDTH   = 110


def apply_size(name: str) -> None:
    global WINDOW_WIDTH, WINDOW_HEIGHT, LOGO_SIZE, STYLESHEET, PCT_WIDTH, RESET_WIDTH
    w, h, logo, tb, te, tp, tr, tt, bh, tw, pw, rw = _SIZES.get(name, _SIZES["compact"])
    PCT_WIDTH   = pw
    RESET_WIDTH = rw
    WINDOW_WIDTH  = w
    WINDOW_HEIGHT = h
    LOGO_SIZE     = logo
    STYLESHEET    = _make_stylesheet(tb, te, tp, tr, tt, bh, tw)


def _make_stylesheet(tb, te, tp, tr, tt, bh, tw) -> str:
    return f"""
QLabel {{
    color: #CBD5E1;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: {tb}px;
    background: transparent;
    border: none;
}}

QLabel#emoji_label {{
    font-size: {te}px;
    min-width: 16px;
}}

QLabel#pct_label {{
    font-size: {tp}px;
    font-weight: 700;
    color: #FFFFFF;
    min-width: 28px;
}}

QLabel#reset_label {{
    font-size: {tr}px;
    color: #CBD5E1;
    padding-left: 4px;
}}

QLabel#error_label {{
    font-size: {tr}px;
    color: #F87171;
}}

QLabel#interval_label {{
    font-size: {tr}px;
    color: #64748B;
}}

QLabel#timer_label {{
    font-size: {tt}px;
    font-weight: 700;
    color: #38BDF8;
    font-family: "Consolas", "Courier New", monospace;
    min-width: {tw}px;
    qproperty-alignment: AlignCenter;
}}

QProgressBar {{
    border: none;
    border-radius: 2px;
    background-color: #1E293B;
    max-height: {bh}px;
    min-height: {bh}px;
}}

QProgressBar::chunk {{
    border-radius: 2px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366F1,
        stop:1 #8B5CF6
    );
}}

QProgressBar[usage="high"]::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #F59E0B,
        stop:1 #EF4444
    );
}}

QMenu {{
    background-color: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 2px;
    font-family: "Segoe UI", sans-serif;
    font-size: {tb + 1}px;
}}

QMenu::item {{
    padding: 4px 16px;
    border-radius: 3px;
}}

QMenu::item:selected {{
    background-color: #334155;
}}
"""


# Valeurs par défaut (compact) — écrasées par apply_size() avant tout import
apply_size("compact")
