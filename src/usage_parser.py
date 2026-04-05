"""
Parsing de la réponse JSON de l'API Claude usage.
Aucune dépendance Qt ni BeautifulSoup — testable en isolation.
"""

from __future__ import annotations

from datetime import datetime, timezone


def parse_usage(data: dict) -> dict:
    """
    Parse la réponse JSON de l'API /api/organizations/{org_id}/usage.

    Retour succès :
        {"ok": True, "session": {"value": int, "label": str}, "weekly": {"value": int, "label": str}}

    Retour échec :
        {"ok": False, "error": str}
    """
    try:
        five_hour = data.get("five_hour") or {}
        seven_day = data.get("seven_day") or {}

        session_value = _clamp(five_hour.get("utilization", 0))
        weekly_value = _clamp(seven_day.get("utilization", 0))

        session_label = _format_resets_at(five_hour.get("resets_at", ""))
        weekly_label = _format_resets_at(seven_day.get("resets_at", ""))

        return {
            "ok": True,
            "session": {"value": session_value, "label": session_label},
            "weekly":  {"value": weekly_value,  "label": weekly_label},
        }

    except Exception:
        return {"ok": False, "error": "unknown"}


def _clamp(value) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return 0


def _format_resets_at(resets_at_str: str) -> str:
    """Convertit un timestamp ISO en durée lisible : 'Réinit. dans 1h30'."""
    if not resets_at_str:
        return ""
    try:
        reset_time = datetime.fromisoformat(resets_at_str)
        now = datetime.now(timezone.utc)
        delta = reset_time - now
        total_seconds = int(delta.total_seconds())

        if total_seconds <= 0:
            return "🔄 imminente"

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"🔄 {hours}h{minutes:02d}"
        return f"🔄 {minutes}min"
    except Exception:
        return resets_at_str
