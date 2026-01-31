# Deployment Guide - Basketball Blitz Bot

## Pre-Deployment Checklist

- [ ] Discord bot token obtained from [Discord Developer Portal](https://discord.com/developers/applications)
- [ ] Bot invite link generated with scopes: `bot` and permissions: `applications.commands`, `send_messages`, `embed_links`, `read_message_history`, `manage_messages`
- [ ] Hosting platform account created (Replit, Railway, Heroku alternative, or self-hosted)
- [ ] `.env` file created with required variables (see Environment Variables section)
- [ ] requirements.txt verified (discord.py>=2.2.0, python-dotenv>=1.0.0)
- [ ] bot.py tested locally with `python bot.py` (should connect and show "Bot is ready")
- [ ] SQLite database initialized (automatic on first run via `persistence.py`)

---

## Environment Variables

Create a `.env` file in the root directory with:

```env
DISCORD_TOKEN=your_bot_token_here
OWNER_ID=123456789  # Your Discord user ID (optional, for test_utils.py)
```

**DO NOT commit `.env` to version control!** It's already in `.gitignore`.

---

## Option 1: Replit (Recommended for Quick Start)

### Setup Steps

1. **Fork/Upload to Replit**
   - Go to [Replit.com](https://replit.com)
   - Click "Create" → "Import from GitHub" (paste repo URL)
   - Or upload files manually

2. **Configure Secrets**
   - Click "Tools" (wrench icon) → "Secrets"
   - Add key: `DISCORD_TOKEN`, value: `your_bot_token_here`
   - Add key: `OWNER_ID`, value: `your_user_id` (optional)

3. **Install Dependencies**
   - Replit auto-detects Python and installs from `requirements.txt`
   - Verify in Shell: `pip list | grep discord`

4. **Run Bot**
   - Click "Run" button (green play icon)
   - Watch logs for "Bot is ready!" message
   - Invite bot to your Discord server using the generated link

5. **Keep Bot Running 24/7**
   - Free Replit projects go offline if inactive for 1 hour
   - Upgrade to Replit Pro ($7/month) for always-on execution
   - Alternative: Use external ping service (UptimeRobot) to keep awake

### Database Persistence on Replit
- SQLite database (`games.db`) stored in project file system
- Persists between restarts automatically
- No additional setup needed

---

## Option 2: Railway (Free Tier Available)

### Setup Steps

1. **Create Railway Account**
   - Go to [Railway.app](https://railway.app)
   - Sign in with GitHub (recommended)

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub"
   - Authorize Railway to access your repo
   - Select the Basketball Blitz repository

3. **Configure Environment**
   - In Railway dashboard, click "Variables"
   - Add:
     - `DISCORD_TOKEN`: `your_bot_token_here`
     - `OWNER_ID`: `your_user_id` (optional)

4. **Deploy**
   - Railway auto-detects Python
   - Installs dependencies from `requirements.txt`
   - Starts bot automatically
   - Watch logs for "Bot is ready!"

5. **Keep Running 24/7**
   - Free tier: Limited free credits (~5/month)
   - $5/month plan provides dedicated monthly allowance
   - Logs available in dashboard

### Database on Railway
- SQLite (`games.db`) stored in ephemeral container file system
- **WARNING**: Database resets when container restarts (every deploy)
- **Solution**: Use Railway PostgreSQL instead
  - Add PostgreSQL service in Railway dashboard
  - Update `persistence.py` to use PostgreSQL (see Advanced section)

---

## Option 3: Self-Hosted (VPS - DigitalOcean, Linode, AWS)

### Setup Steps (Ubuntu/Debian)

1. **SSH into Your Server**
   ```bash
   ssh root@your_server_ip
   ```

2. **Install Python & Dependencies**
   ```bash
   apt update
   apt install python3 python3-pip git
   ```

3. **Clone Repository**
   ```bash
   cd /opt
   git clone https://github.com/yourusername/basketball_blitz.git
   cd basketball_blitz
   ```

4. **Install Python Packages**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Create `.env` File**
   ```bash
   nano .env
   # Add:
   # DISCORD_TOKEN=your_token_here
   # OWNER_ID=your_user_id
   # Save: Ctrl+X → Y → Enter
   ```

6. **Run Bot with Systemd (Auto-Start on Reboot)**

   Create `/etc/systemd/system/basketball-blitz.service`:
   ```ini
   [Unit]
   Description=Basketball Blitz Discord Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/basketball_blitz
   ExecStart=/usr/bin/python3 /opt/basketball_blitz/bot.py
   Restart=always
   RestartSec=10
   Environment="PATH=/usr/local/bin:/usr/bin"
   EnvironmentFile=/opt/basketball_blitz/.env

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   systemctl daemon-reload
   systemctl enable basketball-blitz
   systemctl start basketball-blitz
   ```

   Check status:
   ```bash
   systemctl status basketball-blitz
   journalctl -u basketball-blitz -f  # Live logs
   ```

7. **Database Persistence**
   - SQLite `games.db` stored in `/opt/basketball_blitz/`
   - Persists across restarts automatically
   - Backup regularly:
     ```bash
     cp /opt/basketball_blitz/games.db /backup/games_$(date +%Y%m%d).db
     ```

---

## Option 4: Docker Deployment

### Dockerfile

Create `Dockerfile` in root:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### Docker Compose (Optional)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OWNER_ID=${OWNER_ID}
    volumes:
      - ./games.db:/app/games.db
    restart: always
```

### Run Locally
```bash
docker build -t basketball-blitz .
docker run --env-file .env -v $(pwd)/games.db:/app/games.db basketball-blitz
```

### Deploy to Cloud (e.g., Railway, Render)
- Push Dockerfile to GitHub
- Railway/Render auto-detects Dockerfile
- No `requirements.txt` needed in detection

---

## Testing After Deployment

### 1. Verify Bot Connection
Check bot appears online in Discord server

### 2. Test Basic Commands
```
/newgame
/livescore
```

### 3. Run Full Test Scenario (Optional)
Use [TESTING_QUICK_START.md](./TESTING_QUICK_START.md) with real players

### 4. Check Database
- Replit: File system explorer → `games.db`
- Railway: Use adminer addon or SSH
- Self-hosted: SSH and inspect `/opt/basketball_blitz/games.db`

---

## Monitoring & Maintenance

### Logs
- **Replit**: "Console" tab shows stdout/stderr
- **Railway**: "Logs" tab in dashboard
- **Self-hosted**: `journalctl -u basketball-blitz -f`
- **Docker**: `docker logs -f <container_id>`

### Key Logs to Watch For
```
Bot is ready!                    # ✅ Startup successful
Loaded X games from database     # ✅ Persistence working
on_command_error:                # ❌ Command failed (check next lines)
Database error:                  # ❌ Persistence issue
```

### Database Backups
- **Weekly**: Download `games.db` and store locally
- **Monthly**: Archive old backups
- **Before Updates**: Always backup before redeploying

### Restart Bot
- **Replit**: Click "Stop" → "Run"
- **Railway**: "Redeploy" in dashboard
- **Self-hosted**: `systemctl restart basketball-blitz`
- **Docker**: `docker restart <container_id>`

---

## Troubleshooting

### Bot Goes Offline After 1 Hour
**Symptom**: Works initially, then stops responding
- **Cause**: Replit free tier goes to sleep
- **Fix**: Upgrade to Replit Pro or use Railway/self-hosted

### "Invalid Token" Error on Startup
**Symptom**: `discord.errors.LoginFailure`
- **Cause**: Wrong token or token pasted with extra spaces
- **Fix**: Regenerate token in Discord Developer Portal, verify no extra whitespace

### "Database is locked" Errors
**Symptom**: Random errors during gameplay
- **Cause**: Multiple bot instances accessing same `games.db`
- **Fix**: Ensure only one bot instance running; use process supervisor

### Memory Leak / Bot Slows Over Time
**Symptom**: Increasing memory usage, command latency grows
- **Cause**: In-memory game objects not cleaned up
- **Fix**: Restart bot daily via cron or deployment pipeline

### Commands Not Responding
**Symptom**: Slash commands appear but don't execute
- **Cause**: Bot permissions missing or not synced
- **Fix**:
  1. Re-invite with correct scopes: `applications.commands`, `send_messages`
  2. Restart bot: `systemctl restart basketball-blitz`

---

## Performance Tuning

### For 100+ Players
- SQLite suitable for <1000 concurrent games
- Monitor database size: `ls -lh games.db`
- If >100MB, consider archiving old games:
  ```python
  # In persistence.py, add:
  def archive_old_games(days=30):
      # Move games from before N days to archive table
  ```

### For Multiple Bot Instances
- Use PostgreSQL instead of SQLite (see Advanced section)
- Implement distributed locking via Redis
- Current design assumes single instance per guild

---

## Advanced: PostgreSQL Migration

If scaling beyond 1000 concurrent games:

1. **Install PostgreSQL**
   ```bash
   pip install psycopg2-binary
   ```

2. **Update `persistence.py`**
   ```python
   import psycopg2
   from psycopg2.extras import RealDictCursor
   import os

   DB_URL = os.getenv("DATABASE_URL")  # Railway/Render provide this

   def init_db():
       conn = psycopg2.connect(DB_URL)
       cursor = conn.cursor()
       cursor.execute("""
           CREATE TABLE IF NOT EXISTS games (
               guild_id BIGINT PRIMARY KEY,
               state JSON,
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           )
       """)
       conn.commit()
       conn.close()
   ```

3. **Deploy with PostgreSQL**
   - Railway: "Add Service" → PostgreSQL (auto-creates DATABASE_URL)
   - Render: Create database instance, add connection string

---

## Going Live Checklist

- [ ] Bot deployed and online (check Discord server)
- [ ] `/newgame` and `/join` commands work
- [ ] Database persistent (test by restarting bot)
- [ ] Monitoring/alerting set up (optional)
- [ ] Backup plan for `games.db` in place
- [ ] Team notified of bot availability
- [ ] Test scenario run with 3+ players
- [ ] Known issues documented (see TESTING.md)

---

## Support & Debugging

For deployment issues:
1. Check logs first (key logs section above)
2. Review bot permissions in Discord server settings
3. Verify `.env` file has `DISCORD_TOKEN` without extra spaces
4. Test locally first: `python bot.py` before deploying
5. See TESTING.md for gameplay troubleshooting

---

**Estimated Time to Deploy**: 
- Replit: 5 minutes
- Railway: 10 minutes
- Self-hosted: 20-30 minutes
- Docker: 15 minutes (after image build)

**Estimated Monthly Cost**:
- Replit Free: $0 (with 1-hour sleep)
- Replit Pro: $7/month (always on)
- Railway: $5+/month (with free trial)
- Self-hosted VPS: $5-20/month (DigitalOcean, Linode)
- Discord: $0 (bot is free)
