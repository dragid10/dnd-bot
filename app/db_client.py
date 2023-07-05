from app.db.base_db import BaseDB


class Tracker:
    def __init__(self, db: BaseDB):
        self.db = db
        self.db.connect()

    # ============ Players ============
    def get_players_for_guild(self, guild_id: int):
        return self.db.get_players_for_guild(guild_id)

    # ============ Attendees ============
    def get_attendees_for_guild(self, guild_id: int):
        self.db.get_attendees_for_guild(guild_id)

    # ============ Config ============
    def create_guild_config(self,
                            guild_id: int,
                            voice_channel_id: int,
                            dm_username: str,
                            dm_id: int,
                            session_day: str,
                            session_time: str,
                            meeting_room: int,
                            first_alert: str,
                            second_alert: str):
        self.db.create_guild_config(guild_id=guild_id,
                                    voice_channel_id=voice_channel_id,
                                    dm_username=dm_username,
                                    dm_id=dm_id,
                                    session_day=session_day,
                                    session_time=session_time,
                                    meeting_room=meeting_room,
                                    first_alert=first_alert,
                                    second_alert=second_alert)

    def get_first_alert_configs(self, day_of_week: int) -> list:
        return self.db.get_first_alert_configs(day_of_week)

    def get_second_alert_configs(self, day_of_week: int) -> list:
        return self.db.get_second_alert_configs(day_of_week)

    def is_session_cancelled(self, guild_id: int) -> bool:
        return self.db.is_session_cancelled(guild_id)

    def is_full_group(self, guild_id: int) -> bool:
        return self.db.is_full_group(guild_id)

    def get_unanswered_players(self, guild_id: int) -> list:
        return self.db.get_unanswered_players(guild_id)

    def get_session_day_configs(self, day_of_week: int):
        self.db.get_session_day_configs(day_of_week)
