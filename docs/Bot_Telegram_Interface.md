# Bot — Telegram Interface (Two‑Mode)
Mode selection via /start keyboard:
- Command ⚙️: /tasks, /status, /addtask; logs bot.command.executed
- Intelligence 🧠: free dialog; /result → summary; Save ✅ | Edit ✏️ → memory/intelligence_log/
Security: token only in config/.env; pre‑commit denies secrets.
Health: /ping local response. Default connection mode: polling.
