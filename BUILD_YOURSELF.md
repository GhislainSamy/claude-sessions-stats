# Build Yourself

Ce guide couvre l'installation depuis les sources et la compilation en EXE autonome.

---

## Prérequis

- Python **3.11+**
- Extension navigateur **Tampermonkey** (Firefox ou Chrome)
- Un compte **Claude** actif

---

## Installation depuis les sources

### 1. Cloner le repo

```bash
git clone https://github.com/GhislainSamy/claude-sessions-stats.git
cd claude-sessions-stats
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Installer le userscript Tampermonkey

Cliquer [ici](https://github.com/GhislainSamy/claude-sessions-stats/raw/main//browser/claude_usage_stats_to_desktop.user.js)

> Vous pouvez ajuster `INTERVAL_SEC` dans le script pour changer la fréquence de mise à jour (défaut : 60s).

---

## Compiler en EXE

> Nécessite Windows. L'EXE généré est autonome, aucun Python requis sur la machine cible.

```bat
build.bat
```

L'exécutable est généré dans `dist/claude_stats.exe`, accompagné de `config.ini`.
