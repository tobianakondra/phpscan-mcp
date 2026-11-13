# MCP Deployment — php-legacy-auditor

Ce document décrit comment lancer et connecter le serveur MCP `php-legacy-auditor` aux clients/agents IA :
**OpenCode**, **Claude Desktop**, **Kiro CLI** et **Agy**.

Il couvre :

1. L'environnement Python définitif (venv persistant dans le projet).
2. Le test en une ligne de terminal.
3. Les blocs de configuration JSON pour chaque client.
4. La gestion de la variable `ALLOWED_AUDIT_ROOT` pour changer de dossier cible.

---

## 1. Environnement définitif

Le venv `/tmp/audit-venv` n'est pas persistant. Créez un venv dans le dossier du projet puis installez le package en mode éditable.

```bash
cd /home/richard/tree/phpscan-mcp

# Supprimer l'ancien venv temporaire s'il reste
rm -rf /tmp/audit-venv

# Créer le venv persistant
python3 -m venv .venv

# Mettre à jour pip/setuptools/wheel
.venv/bin/pip install --quiet --upgrade pip setuptools wheel

# Installer le package en mode éditable + mcp<2 (FastMCP requis)
.venv/bin/pip install --quiet -e . "mcp<2"
```

Vérification :

```bash
cd /home/richard/tree/phpscan-mcp
.venv/bin/python -c "import sys; print(sys.prefix); print(sys.executable)"
.venv/bin/python -c "import php_legacy_auditor; print(php_legacy_auditor.__file__)"
```

État attendu :

```text
/home/richard/tree/phpscan-mcp/.venv
/home/richard/tree/phpscan-mcp/.venv/bin/python
/home/richard/tree/phpscan-mcp/src/php_legacy_auditor/__init__.py
```

### Binaires d'analyse

Le projet fournit déjà :

- `vendor/bin/psalm`
- `vendor/bin/progpilot`

Si vous utilisez **Semgrep** ou **PHPCS**, assurez-vous qu'ils sont dans le `PATH` du `.venv` ou installés dans le projet :

```bash
.venv/bin/pip install --quiet semgrep
.venv/bin/pip install --quiet phpcodesniffer
```

---

## 2. Test en une ligne de terminal

Testez que le serveur démarre sans erreur `PYTHONPATH` ni dépendances manquantes :

```bash
cd /home/richard/tree/phpscan-mcp && PYTHONPATH=src .venv/bin/python -c "from php_legacy_auditor.server import mcp; print('OK:', mcp)" 2>&1
```

Résultat attendu :

```text
OK: <mcp.server.fastmcp.server.FastMCP object at 0x...>
```

Lancer le serveur en stdio (mode serveur, attend la connexion MCP) :

```bash
cd /home/richard/tree/phpscan-mcp
PYTHONPATH=src .venv/bin/python -m php_legacy_auditor.server
```

Le serveur expose ces outils :

- `map_project_structure`
- `read_code_context`
- `run_semgrep_scan`
- `run_psalm_scan`
- `run_progpilot_scan`
- `run_phpcs_scan`

---

## 3. Configuration par client

Les clients se connectent en `stdio`. Le dossier de travail doit être le projet et `PYTHONPATH` doit pointer vers `src`. La variable `ALLOWED_AUDIT_ROOT` limite le dossier cible.

### Variables communes

```bash
export ALLOWED_AUDIT_ROOT="/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app"
# ou le site PHP legacy après : "/home/richard/tree/phpscan-mcp/site_legacy"
export PYTHONPATH="/home/richard/tree/phpscan-mcp/src"
```

---

### OpenCode

Fichier : `~/.config/opencode/opencode.jsonc` (ou `opencode.jsonc`)

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcpServers": {
    "php-legacy-auditor": {
      "command": "/home/richard/tree/phpscan-mcp/.venv/bin/python",
      "args": [
        "-m",
        "php_legacy_auditor.server"
      ],
      "env": {
        "PYTHONPATH": "/home/richard/tree/phpscan-mcp/src",
        "ALLOWED_AUDIT_ROOT": "/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app"
      }
    }
  }
}
```

Après modification, redémarrez OpenCode.

---

### Claude Desktop

Fichier : `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS),
`%APPDATA%\Claude\claude_desktop_config.json` (Windows),
`~/.config/claude/claude_desktop_config.json` (Linux)

```json
{
  "mcpServers": {
    "php-legacy-auditor": {
      "command": "/home/richard/tree/phpscan-mcp/.venv/bin/python",
      "args": [
        "-m",
        "php_legacy_auditor.server"
      ],
      "env": {
        "PYTHONPATH": "/home/richard/tree/phpscan-mcp/src",
        "ALLOWED_AUDIT_ROOT": "/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app"
      }
    }
  }
}
```

Redémarrez Claude Desktop.

---

### Kiro CLI / Agy

Ces clients utilisent généralement la même convention MCP : un fichier de configuration avec un bloc `mcpServers`.

Fichier exemple : `mcp_config.json` (à placer où le client attend).

```json
{
  "mcpServers": {
    "php-legacy-auditor": {
      "command": "/home/richard/tree/phpscan-mcp/.venv/bin/python",
      "args": [
        "-m",
        "php_legacy_auditor.server"
      ],
      "env": {
        "PYTHONPATH": "/home/richard/tree/phpscan-mcp/src",
        "ALLOWED_AUDIT_ROOT": "/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app"
      }
    }
  }
}
```

Si le client expose une commande d'enregistrement CLI, utilisez-la avec les mêmes valeurs :

```bash
mcp register --name php-legacy-auditor \
  --command "/home/richard/tree/phpscan-mcp/.venv/bin/python" \
  --args "-m" "php_legacy_auditor.server" \
  --env "PYTHONPATH=/home/richard/tree/phpscan-mcp/src" \
  --env "ALLOWED_AUDIT_ROOT=/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app"
```

> Vérifiez la commande exacte de votre client : Kiro CLI et Agy n'ont pas tous deux la même commande d'enregistrement. Ce bloc concerne la configuration standard MCP ou l'équivalent CLI fourni par le client.

---

## 4. Changer le dossier cible (`ALLOWED_AUDIT_ROOT`)

La variable `ALLOWED_AUDIT_ROOT` est lue par le serveur au démarrage depuis l'environnement du processus MCP. Elle est configurable sans modifier le code.

### Principe

`server.py` utilise `ALLOWED_AUDIT_ROOT = os.environ.get("ALLOWED_AUDIT_ROOT")`. Les outils capturent la valeur du processus au lancement, pas à l'appel tool.

### Changement rapide

1. Modifier la valeur `ALLOWED_AUDIT_ROOT` dans le fichier de configuration du client.
2. Redémarrer le client.
3. Vérifier que le dossier existe :

```bash
ls -ld "/chemin/vers/le/dossier/cible"
```

4. Lancer ou relancer la connexion MCP.

### Exemple : passer de l'échantillon au site legacy

```json
{
  "mcpServers": {
    "php-legacy-auditor": {
      "command": "/home/richard/tree/phpscan-mcp/.venv/bin/python",
      "args": [
        "-m",
        "php_legacy_auditor.server"
      ],
      "env": {
        "PYTHONPATH": "/home/richard/tree/phpscan-mcp/src",
        "ALLOWED_AUDIT_ROOT": "/home/richard/tree/phpscan-mcp/site_legacy"
      }
    }
  }
}
```

### Règles de sécurité

Le serveur valide chaque cible avec `validate_safe_path` : si le dossier cible ne se trouve pas dans `ALLOWED_AUDIT_ROOT`, les outils retournent une erreur du type :

```text
Path ... resolves outside ALLOWED_AUDIT_ROOT ...
```

C'est un garde-fou qui empêche de scanner un dossier en dehors du répertoire autorisé.

---

## 5. Exemple de canal de travail

```bash
# 1. Lancer le serveur
cd /home/richard/tree/phpscan-mcp
PYTHONPATH=src .venv/bin/python -m php_legacy_auditor.server

# 2. Depuis le client, demander la cartographie
map_project_structure(target_dir="/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app")

# 3. Lancer les scans
run_semgrep_scan(target="/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app")
run_psalm_scan(target="/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app")
run_progpilot_scan(target="/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app")
run_phpcs_scan(target="/home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app", standard="PSR12")
```

---

## 6. Résumé des chemins

```text
Projet racine                : /home/richard/tree/phpscan-mcp
Venv persistant              : /home/richard/tree/phpscan-mcp/.venv/bin/python
Package éditable             : /home/richard/tree/phpscan-mcp
Module serveur               : /home/richard/tree/phpscan-mcp/src/php_legacy_auditor/server.py
Entrée                       : python -m php_legacy_auditor.server
PYTHONPATH requis            : /home/richard/tree/phpscan-mcp/src
Dossier cible par défaut     : /home/richard/tree/phpscan-mcp/tests/sample_vulnerable_app
Dossier cible possible       : /home/richard/tree/phpscan-mcp/site_legacy
