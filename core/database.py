import aiosqlite
import json


class Database:
    def __init__(self):
        self.db_path = "bot_data.db"

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id               INTEGER PRIMARY KEY,
                    log_channel_id         INTEGER,
                    jail_role_id           INTEGER,
                    jailticket_category_id INTEGER,
                    jail_channel_id        INTEGER,
                    support_category_id    INTEGER,
                    allowed_roles          TEXT DEFAULT '[]'
                );
                CREATE TABLE IF NOT EXISTS moderation_cases (
                    case_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id     INTEGER NOT NULL,
                    user_id      INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    action       TEXT NOT NULL,
                    reason       TEXT,
                    timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS afk_users (
                    user_id    INTEGER PRIMARY KEY,
                    guild_id   INTEGER,
                    reason     TEXT,
                    since      INTEGER
                );
                CREATE TABLE IF NOT EXISTS jail_roles (
                    user_id  INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    role_ids TEXT NOT NULL,
                    PRIMARY KEY (user_id, guild_id)
                );
                CREATE TABLE IF NOT EXISTS vcbans (
                    guild_id INTEGER NOT NULL,
                    user_id  INTEGER NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id   INTEGER NOT NULL,
                    user_id    INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    type       TEXT NOT NULL,
                    opened_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS jail_panel (
                    guild_id    INTEGER PRIMARY KEY,
                    channel_id  INTEGER,
                    message_id  INTEGER
                );
            """)

            # Safe column migrations
            try:
                await db.execute("ALTER TABLE afk_users ADD COLUMN since INTEGER")
            except Exception:
                pass

            new_columns = [
                ("log_mute_id",        "INTEGER"),
                ("log_ban_id",         "INTEGER"),
                ("log_role_id",        "INTEGER"),
                ("log_music_id",       "INTEGER"),
                ("log_voice_id",       "INTEGER"),
                ("log_ticket_id",      "INTEGER"),
                ("log_jail_id",        "INTEGER"),
                ("jail_channel_id",    "INTEGER"),
                ("log_member_id",      "INTEGER"),
                ("log_message_id",     "INTEGER"),
                ("log_server_id",      "INTEGER"),
                ("log_channel_log_id", "INTEGER"),
                ("owner_second_acc_id","INTEGER"),
            ]
            for col, coltype in new_columns:
                try:
                    await db.execute(f"ALTER TABLE guild_settings ADD COLUMN {col} {coltype}")
                except Exception:
                    pass

            await db.commit()

    # ── Guild Settings ────────────────────────────────────────────────────────
    async def _get(self, guild_id, key):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(f"SELECT {key} FROM guild_settings WHERE guild_id=?", (guild_id,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def _set(self, guild_id, key, value):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                INSERT INTO guild_settings (guild_id, {key}) VALUES (?,?)
                ON CONFLICT(guild_id) DO UPDATE SET {key}=excluded.{key}
            """, (guild_id, value))
            await db.commit()

    async def get_log_channel(self, guild_id):         return await self._get(guild_id, "log_channel_id")
    async def set_log_channel(self, guild_id, v):      await self._set(guild_id, "log_channel_id", v)
    async def get_log_mute(self, guild_id):            return await self._get(guild_id, "log_mute_id")
    async def set_log_mute(self, guild_id, v):         await self._set(guild_id, "log_mute_id", v)
    async def get_log_ban(self, guild_id):             return await self._get(guild_id, "log_ban_id")
    async def set_log_ban(self, guild_id, v):          await self._set(guild_id, "log_ban_id", v)
    async def get_log_role(self, guild_id):            return await self._get(guild_id, "log_role_id")
    async def set_log_role(self, guild_id, v):         await self._set(guild_id, "log_role_id", v)
    async def get_log_music(self, guild_id):           return await self._get(guild_id, "log_music_id")
    async def set_log_music(self, guild_id, v):        await self._set(guild_id, "log_music_id", v)
    async def get_log_voice(self, guild_id):           return await self._get(guild_id, "log_voice_id")
    async def set_log_voice(self, guild_id, v):        await self._set(guild_id, "log_voice_id", v)
    async def get_log_ticket(self, guild_id):          return await self._get(guild_id, "log_ticket_id")
    async def set_log_ticket(self, guild_id, v):       await self._set(guild_id, "log_ticket_id", v)
    async def get_log_jail(self, guild_id):            return await self._get(guild_id, "log_jail_id")
    async def set_log_jail(self, guild_id, v):         await self._set(guild_id, "log_jail_id", v)
    async def get_log_member(self, guild_id):          return await self._get(guild_id, "log_member_id")
    async def set_log_member(self, guild_id, v):       await self._set(guild_id, "log_member_id", v)
    async def get_log_message(self, guild_id):         return await self._get(guild_id, "log_message_id")
    async def set_log_message(self, guild_id, v):      await self._set(guild_id, "log_message_id", v)
    async def get_log_server(self, guild_id):          return await self._get(guild_id, "log_server_id")
    async def set_log_server(self, guild_id, v):       await self._set(guild_id, "log_server_id", v)
    async def get_log_channel_log(self, guild_id):     return await self._get(guild_id, "log_channel_log_id")
    async def set_log_channel_log(self, guild_id, v):  await self._set(guild_id, "log_channel_log_id", v)
    async def get_jail_role(self, guild_id):           return await self._get(guild_id, "jail_role_id")
    async def set_jail_role(self, guild_id, v):        await self._set(guild_id, "jail_role_id", v)
    async def get_jailticket_cat(self, guild_id):      return await self._get(guild_id, "jailticket_category_id")
    async def set_jailticket_cat(self, guild_id, v):   await self._set(guild_id, "jailticket_category_id", v)
    async def get_jail_channel(self, guild_id):        return await self._get(guild_id, "jail_channel_id")
    async def set_jail_channel(self, guild_id, v):     await self._set(guild_id, "jail_channel_id", v)
    async def get_support_cat(self, guild_id):         return await self._get(guild_id, "support_category_id")
    async def set_support_cat(self, guild_id, v):      await self._set(guild_id, "support_category_id", v)

    async def get_allowed_roles(self, guild_id) -> list:
        raw = await self._get(guild_id, "allowed_roles")
        return json.loads(raw) if raw else []

    async def set_allowed_roles(self, guild_id, role_ids: list):
        await self._set(guild_id, "allowed_roles", json.dumps(role_ids))

    # ── Moderation Cases ──────────────────────────────────────────────────────
    async def add_case(self, guild_id, user_id, mod_id, action, reason) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "INSERT INTO moderation_cases(guild_id,user_id,moderator_id,action,reason) VALUES(?,?,?,?,?)",
                (guild_id, user_id, mod_id, action, reason)
            )
            await db.commit()
            return cur.lastrowid

    async def get_warnings(self, guild_id, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT case_id,moderator_id,reason,timestamp FROM moderation_cases "
                "WHERE guild_id=? AND user_id=? AND action='Warn' ORDER BY timestamp DESC",
                (guild_id, user_id))
            return await cur.fetchall()

    async def get_cases(self, guild_id, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT case_id,action,moderator_id,reason,timestamp FROM moderation_cases "
                "WHERE guild_id=? AND user_id=? ORDER BY timestamp DESC",
                (guild_id, user_id))
            return await cur.fetchall()

    async def get_actions_by_mod(self, guild_id, mod_id):
        """Get all moderation actions taken BY a specific moderator."""
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT case_id,action,user_id,reason,timestamp FROM moderation_cases "
                "WHERE guild_id=? AND moderator_id=? ORDER BY timestamp DESC",
                (guild_id, mod_id))
            return await cur.fetchall()

    async def delete_case(self, case_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM moderation_cases WHERE case_id=?", (case_id,))
            await db.commit()

    # ── AFK ───────────────────────────────────────────────────────────────────
    async def get_afk(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT reason, since FROM afk_users WHERE user_id=?", (user_id,))
            return await cur.fetchone()

    async def set_afk(self, user_id, guild_id, reason):
        import time
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO afk_users(user_id,guild_id,reason,since) VALUES(?,?,?,?)",
                             (user_id, guild_id, reason, int(time.time())))
            await db.commit()

    async def remove_afk(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM afk_users WHERE user_id=?", (user_id,))
            await db.commit()

    # ── Jail Roles ────────────────────────────────────────────────────────────
    async def set_jail_roles(self, user_id, guild_id, role_ids: list):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO jail_roles(user_id,guild_id,role_ids) VALUES(?,?,?)",
                             (user_id, guild_id, json.dumps(role_ids)))
            await db.commit()

    async def get_jail_roles(self, user_id, guild_id) -> list:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT role_ids FROM jail_roles WHERE user_id=? AND guild_id=?",
                                   (user_id, guild_id))
            row = await cur.fetchone()
            return json.loads(row[0]) if row else []

    async def clear_jail_roles(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM jail_roles WHERE user_id=? AND guild_id=?", (user_id, guild_id))
            await db.commit()

    # ── VC Bans ───────────────────────────────────────────────────────────────
    async def add_vcban(self, guild_id, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO vcbans(guild_id,user_id) VALUES(?,?)", (guild_id, user_id))
            await db.commit()

    async def remove_vcban(self, guild_id, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM vcbans WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            await db.commit()

    async def is_vcbanned(self, guild_id, user_id) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT 1 FROM vcbans WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            return await cur.fetchone() is not None

    # ── Tickets ───────────────────────────────────────────────────────────────
    async def open_ticket(self, guild_id, user_id, channel_id, ticket_type) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "INSERT INTO tickets(guild_id,user_id,channel_id,type) VALUES(?,?,?,?)",
                (guild_id, user_id, channel_id, ticket_type))
            await db.commit()
            return cur.lastrowid

    async def get_ticket_by_channel(self, channel_id):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT * FROM tickets WHERE channel_id=?", (channel_id,))
            return await cur.fetchone()

    async def close_ticket(self, channel_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM tickets WHERE channel_id=?", (channel_id,))
            await db.commit()

    # ── Jail Panel ────────────────────────────────────────────────────────────
    async def set_jail_panel(self, guild_id, channel_id, message_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO jail_panel(guild_id,channel_id,message_id) VALUES(?,?,?)",
                (guild_id, channel_id, message_id))
            await db.commit()

    async def get_jail_panel(self, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT channel_id,message_id FROM jail_panel WHERE guild_id=?", (guild_id,))
            return await cur.fetchone()

    # ── Owner Second Account ──────────────────────────────────────────────────
    async def get_owner_second_acc(self, guild_id):
        return await self._get(guild_id, "owner_second_acc_id")

    async def set_owner_second_acc(self, guild_id, user_id):
        await self._set(guild_id, "owner_second_acc_id", user_id)
