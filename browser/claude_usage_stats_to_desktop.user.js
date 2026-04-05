// ==UserScript==
// @name         Claude Usage Stats → Desktop
// @namespace    https://github.com/GhislainSamy/claude-sessions-stats
// @version      1.0
// @description  Envoie les stats d'usage Claude au widget desktop toutes les N secondes
// @match        https://claude.ai/settings/usage
// @grant        GM_xmlhttpRequest
// @connect      localhost
// ==/UserScript==

(function () {
    'use strict';

    // ── Configuration ──────────────────────────────────────────────
    const LOCAL_PORT = 7842;  // Doit correspondre à config.ini [server] port
    const INTERVAL_SEC = 30;  // Intervalle de rafraîchissement en secondes
    // ───────────────────────────────────────────────────────────────

    function getOrgId() {
        const match = document.cookie.match(/(?:^|;\s*)lastActiveOrg=([a-f0-9\-]+)/);
        return match ? match[1] : null;
    }

    function fetchUsage() {
        const orgId = getOrgId();
        if (!orgId) {
            console.warn('[Claude Stats] lastActiveOrg introuvable dans les cookies.');
            return;
        }

        fetch(`https://claude.ai/api/organizations/${orgId}/usage`, {
            credentials: 'include',
            headers: {
                'Accept': '*/*',
                'Accept-Language': 'fr,fr-FR;q=0.9,en-US;q=0.8,en;q=0.7',
                'anthropic-client-platform': 'web_claude_ai',
                'anthropic-client-version': '1.0.0',
                'content-type': 'application/json',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            },
            method: 'GET',
            mode: 'cors',
        })
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            GM_xmlhttpRequest({
                method: 'POST',
                url: `http://localhost:${LOCAL_PORT}/usage`,
                headers: { 'Content-Type': 'application/json' },
                data: JSON.stringify({ ...data, interval_sec: INTERVAL_SEC }),
                onerror: () => console.warn('[Claude Stats] Widget injoignable sur le port', LOCAL_PORT),
            });
        })
        .catch(err => console.warn('[Claude Stats] Erreur fetch:', err));
    }

    // Premier appel immédiat, puis toutes les N secondes
    fetchUsage();
    setInterval(fetchUsage, INTERVAL_SEC * 1000);

})();
