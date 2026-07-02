# Deployment (for whoever runs this on the server)

This script is a **one-shot batch job**, not a service or daemon. Each run:
fetch PDFs from Drive -> check sheet -> write results -> exit. It should be
triggered on a schedule (e.g. every 30 minutes), not run continuously.

A typical run takes well under a minute (see `logs/report_checker.log` for
timing). Running it every 30 min uses a negligible fraction of Google's API
quota (300 read requests/min per project) and negligible server resources.

## Setup (one time)

```bash
git clone <this repo>
cd Report_checker
pip install -r requirements.txt
cp .env.example .env
# fill in .env: GOOGLE_DRIVE_FOLDER_ID, GOOGLE_SHEET_ID, WORKSHEET_NAME
# place credentials/service_account.json (see README.md)
```

## Option A — cron (simplest, Linux)

Run every 30 minutes:

```bash
crontab -e
```

Add:

```
*/30 * * * * cd /path/to/Report_checker && /usr/bin/python3 main.py >> logs/cron.log 2>&1
```

## Option B — systemd timer (more robust: retries, logs to journalctl)

`/etc/systemd/system/report-checker.service`:

```ini
[Unit]
Description=Report Checker

[Service]
Type=oneshot
WorkingDirectory=/path/to/Report_checker
ExecStart=/usr/bin/python3 main.py
```

`/etc/systemd/system/report-checker.timer`:

```ini
[Unit]
Description=Run Report Checker every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now report-checker.timer
sudo systemctl list-timers report-checker.timer   # confirm schedule
journalctl -u report-checker.service -f           # watch logs live
```

## Notes for tech support

- No need to keep a process running — the timer/cron handles scheduling.
- `logs/report_checker.log` grows over time; consider adding a `logrotate`
  entry if this runs long-term (not included here, low priority at low
  frequency).
- `.env` and `credentials/service_account.json` are not in git — they need
  to be created directly on the server (see README.md for what goes in each).
- Exit code is non-zero on failure (see `main.py`), so cron/systemd failure
  alerts will fire correctly if something breaks.
