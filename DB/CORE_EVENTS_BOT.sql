-- Views and helpers for BOT/Telegram events
CREATE OR REPLACE VIEW core.v_bot_events AS
SELECT * FROM core.events WHERE event_type LIKE 'bot.%';

-- Expected bot.*:
-- bot.telegram.connected, bot.command.executed, bot.intelligence.result.saved
