# Operations & Monitoring Guide - Basketball Blitz

## Daily Operations

### Startup Checklist
- [ ] Bot is online in Discord server
- [ ] Check recent logs for errors
- [ ] Verify database size hasn't exploded (>500MB is suspicious)

### Before/After Scheduled Events
- **Before Tournament**: Backup `games.db`
- **After Tournament**: Archive old games, review balance feedback

---

## Monitoring Metrics

### Health Checks (Every Hour)

1. **Bot Heartbeat**
   - Bot should appear as online in Discord
   - Last activity timestamp in logs

2. **Command Response Time**
   - Target: <500ms for slash commands
   - Acceptable: <2s (Discord's timeout limit)
   - If >3s consistently: Database or memory issue

3. **Error Rate**
   - Target: <0.1% of commands fail
   - Monitor: `on_command_error` logs
   - If >1%: Investigate recent changes

4. **Database Size**
   - Track: `ls -lh games.db` output
   - Growth rate: Should add ~50KB per game
   - If >1GB: Archive old games

### Weekly Reports

- Number of active games
- Number of completed games
- Error patterns (if any)
- Player feedback summaries

---

## Performance Baselines

### Expected Metrics (Single Instance, <100 Players)

| Metric | Target | Acceptable | Alert |
|--------|--------|-----------|-------|
| Command response | <200ms | <500ms | >2s |
| Startup time | <5s | <10s | >20s |
| Memory usage | 50MB | 100MB | >200MB |
| Database size | 1MB / 20 games | 1MB / 15 games | Growing at >5MB/day |
| Uptime | 99.9% | 99% | <98% |

### When to Scale
- **Concurrent games >50**: Monitor for slowdown
- **Concurrent players >300**: Consider database optimization
- **Monthly errors >1%**: Review error logs and deploy fix
- **Memory >300MB**: Restart bot, investigate for leaks

---

## Common Issues & Quick Fixes

### Issue 1: Bot Offline but Process Running

**Symptoms**:
- Bot appears offline in Discord
- Process is running (systemctl shows active)
- No connection errors in logs

**Diagnosis**:
```bash
# Self-hosted
systemctl status basketball-blitz
tail -20 /var/log/syslog | grep basketball

# Docker
docker logs -f <container>
```

**Fix**:
1. Restart bot: `systemctl restart basketball-blitz`
2. Check bot token is valid in `.env`
3. Verify Discord API status: https://status.discord.com
4. If still offline, regenerate bot token in Developer Portal

---

### Issue 2: "Database is Locked" Errors

**Symptoms**:
- Random `sqlite3.OperationalError: database is locked` during gameplay
- Commands work sometimes, fail other times
- Affects all players in active games

**Diagnosis**:
```bash
# Check for multiple bot instances
ps aux | grep "python.*bot.py"

# Check database file locks (Linux)
lsof | grep games.db
```

**Fix**:
1. Ensure only ONE bot instance is running
2. Kill duplicate processes: `killall python` (if safe)
3. Restart bot: `systemctl restart basketball-blitz`
4. If persists: Rebuild database:
   ```bash
   rm games.db  # WARNING: Deletes all active games!
   python3 -c "from persistence import init_db; init_db()"
   systemctl restart basketball-blitz
   ```

---

### Issue 3: Memory Usage Growing

**Symptoms**:
- `top` or Task Manager shows memory growing over hours/days
- Bot becomes slow after long uptime
- Commands timeout frequently

**Diagnosis**:
```bash
# Check memory over time
watch -n 60 'ps aux | grep bot.py | grep -v grep'

# Check for lingering objects in logs
grep -i "timeout\|error" basketball_blitz.log | tail -20
```

**Fix** (Quick):
1. Restart bot: `systemctl restart basketball-blitz`
2. Clear old game data: Run maintenance script (see below)

**Fix** (Permanent):
- Add garbage collection to `bot.py`:
  ```python
  import gc
  
  @tasks.loop(hours=1)
  async def gc_task():
      gc.collect()
      logger.info(f"Memory: {psutil.Process().memory_info().rss / 1024**2:.0f}MB")
  ```

---

### Issue 4: Commands Not Appearing or Working

**Symptoms**:
- Slash commands not visible in Discord
- Commands work sometimes but not always
- "Interaction failed" error messages

**Diagnosis**:
1. Check bot permissions: Verify bot has "Use Slash Commands" permission
2. Check bot role: Ensure bot role is above all user roles
3. Sync commands: Slash commands sync on startup; check logs for "Synced X commands"

**Fix**:
1. Re-invite bot with correct scopes:
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=274878023680&scope=bot%20applications.commands
   ```
   (Permissions: Send Messages, Embed Links, Read Message History, Manage Messages)

2. Restart bot: `systemctl restart basketball-blitz`

3. Wait 10 seconds, try slash command again

---

### Issue 5: Database Corrupted

**Symptoms**:
- "database disk image malformed" or similar SQLite errors
- Bot won't start with `sqlite3.DatabaseError`
- Unable to access games

**Diagnosis**:
```bash
# Try to query database
sqlite3 games.db "SELECT COUNT(*) FROM games;"
```

**Fix** (With Data Loss):
1. Restore from backup: `cp games_backup.db games.db`
2. Restart bot

**Fix** (Without Backup)**:
1. Delete corrupted database: `rm games.db`
2. Restart bot (auto-creates fresh database)
3. Notify players of lost game data

---

## Maintenance Scripts

### Weekly Backup Script

Create `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backup/basketball-blitz"
mkdir -p $BACKUP_DIR
cp /opt/basketball_blitz/games.db $BACKUP_DIR/games_$(date +%Y%m%d_%H%M%S).db
# Keep only last 30 days
find $BACKUP_DIR -name "games_*" -mtime +30 -delete
echo "Backup completed at $(date)"
```

Schedule with cron:
```bash
# Every day at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/basketball-blitz-backup.log 2>&1
```

---

### Monthly Cleanup Script

Create `cleanup.py`:
```python
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "games.db"
ARCHIVE_DAYS = 30

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Archive old games (older than ARCHIVE_DAYS)
cutoff = (datetime.now() - timedelta(days=ARCHIVE_DAYS)).isoformat()

# Check old games
cursor.execute("SELECT COUNT(*) FROM games WHERE created_at < ?", (cutoff,))
old_count = cursor.fetchone()[0]
print(f"Found {old_count} games older than {ARCHIVE_DAYS} days")

# Delete old games (or implement archive table first)
# cursor.execute("DELETE FROM games WHERE created_at < ?", (cutoff,))
# conn.commit()

conn.close()
```

Run monthly:
```bash
python3 cleanup.py
```

---

## Alerting Setup

### UptimeRobot (Replit/Railway Free Alternative)

1. Go to [UptimeRobot.com](https://uptimerobot.com)
2. Create free account
3. Add Monitor:
   - Type: "Keyword"
   - URL: Your bot's invite link or test endpoint
   - Keywords: "online" or equivalent
   - Check interval: 5 minutes

4. Set Alert: Email when bot offline for >15 minutes

---

### Self-Hosted Monitoring (Prometheus + Grafana)

Advanced setup for serious deployments:

1. **Add Prometheus client to bot.py**:
   ```python
   from prometheus_client import Counter, start_http_server
   
   commands_executed = Counter('commands_total', 'Total commands executed')
   command_errors = Counter('command_errors_total', 'Total command errors')
   
   start_http_server(8000)  # Expose metrics on :8000/metrics
   ```

2. **Scrape metrics** in Prometheus
3. **Visualize** in Grafana
4. **Alert** on high error rates or downtime

---

## Update & Deployment

### Deploying New Code

1. **Test locally**:
   ```bash
   python bot.py  # Verify no crashes
   ```

2. **Backup database**:
   ```bash
   cp games.db games_backup.db
   ```

3. **Pull latest code**:
   ```bash
   git pull origin main
   ```

4. **Restart bot**:
   ```bash
   systemctl restart basketball-blitz
   ```

5. **Verify logs**:
   ```bash
   journalctl -u basketball-blitz -n 50
   # Should show "Bot is ready!" and "Loaded X games"
   ```

### Rollback Plan

If deployment breaks:

```bash
# Revert code
git revert HEAD
git push origin main

# Restore database if changed
cp games_backup.db games.db

# Restart
systemctl restart basketball-blitz
```

---

## Performance Tuning

### For Higher Concurrency (100+ Simultaneous Games)

1. **Increase SQLite Performance**:
   ```python
   # In persistence.py, add to init_db():
   cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
   cursor.execute("PRAGMA cache_size=10000")
   cursor.execute("PRAGMA synchronous=NORMAL")
   ```

2. **Implement Connection Pooling** (if scaling further):
   ```python
   from sqlite3 import connect
   from threading import Lock
   
   class ConnectionPool:
       def __init__(self, db_path, pool_size=5):
           self.db_path = db_path
           self.lock = Lock()
   ```

3. **Monitor Bottlenecks**:
   ```bash
   # Identify slow queries
   # Add timing to persistence.py
   import time
   
   start = time.time()
   # ... database operation ...
   duration = time.time() - start
   if duration > 0.1:  # Log slow queries >100ms
       logger.warning(f"Slow query: {duration:.2f}s")
   ```

---

## Disaster Recovery

### Worst-Case Scenarios

| Scenario | Impact | Recovery Time | Data Loss |
|----------|--------|---|---|
| Bot process crashes | No gameplay for 1-5 min | <1 min (auto-restart) | None |
| Server loses power | Complete outage | 5-15 min | None (SQLite safe) |
| Disk fills up | Bot can't save games | <1 min (free disk) | Potentially all active games |
| `games.db` corrupted | Complete failure | 30 min (restore backup) | Last backup interval |
| Hosting account hacked | Bot taken over | 10 min (revoke token) | Potential (change token) |
| Discord API outage | Bot offline | Depends on Discord | None |

### Recovery Procedures

1. **Immediate Actions**:
   - Notify players of outage
   - Assess what's broken (bot? database? hosting?)
   - Have backup `games.db` ready

2. **Restart Bot** (5 mins):
   ```bash
   systemctl restart basketball-blitz
   journalctl -u basketball-blitz -f
   ```

3. **Restore from Backup** (10 mins):
   ```bash
   cp games_backup.db games.db
   systemctl restart basketball-blitz
   ```

4. **Full Redeployment** (20 mins):
   ```bash
   git pull origin main
   pip install -r requirements.txt
   systemctl restart basketball-blitz
   ```

5. **Communicate**:
   - Announce restoration time
   - Resume gameplay
   - Gather feedback on impact

---

## Logs & Debugging

### Log Levels

Add to `bot.py` for more detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # or INFO, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('basketball_blitz.log'),
        logging.StreamHandler()
    ]
)
```

### Key Log Messages

- **"Bot is ready!"** → Bot connected successfully
- **"Loaded X games from database"** → Persistence working
- **"Synced X commands"** → Slash commands ready
- **"on_command_error:"** → Command failed (check next lines for reason)
- **"Database error:"** → SQLite issue

### Enable Debug Logging

```python
# In bot.py, before bot.run():
discord.utils.setup_logging()
```

---

## Conclusion

Regular monitoring, backups, and quick incident response keep Basketball Blitz running smoothly. For most cases:
1. Check logs first
2. Restart bot
3. Restore from backup if data lost
4. Document what happened for future reference

For 24/7 reliability, invest in:
- Automated backups (daily)
- Uptime monitoring (UptimeRobot)
- Restart-on-failure (systemd handles this)
- Status page for players (optional)
