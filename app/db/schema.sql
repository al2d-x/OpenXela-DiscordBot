CREATE TABLE IF NOT EXISTS counters (
    guild_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value INTEGER NOT NULL,
    UNIQUE(guild_id, key)
);
