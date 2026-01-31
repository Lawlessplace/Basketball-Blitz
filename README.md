Basketball Blitz — Discord bot (Python)

Quick start

1. Create a virtualenv and activate it.

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Provide your bot token (recommended via env):

```bash
# Windows (PowerShell)
$env:DISCORD_TOKEN = "YOUR_TOKEN"
# or create a .env with DISCORD_TOKEN=...
```

4. Run the bot

```bash
python bot.py
```

Notes
- Do NOT commit your token (see `.gitignore`).
- Next steps: add persistence, economy, balance gameplay.
