CREATE TABLE IF NOT EXISTS guild_config (
    guild_id TEXT PRIMARY KEY,
    temp_category_id TEXT NULL
);

CREATE TABLE IF NOT EXISTS hub_channels (
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL UNIQUE,
    created_by_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (guild_id, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_hub_channels_guild_id
    ON hub_channels(guild_id);

CREATE TABLE IF NOT EXISTS managed_voice_channels (
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL UNIQUE,
    owner_user_id TEXT NOT NULL,
    hub_channel_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    pending_delete_at TEXT NULL,
    name TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_managed_voice_channels_guild_id
    ON managed_voice_channels(guild_id);
