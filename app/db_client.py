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
        return self.db.get_attendees_for_guild(guild_id)

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
        return self.db.get_session_day_configs(day_of_week)

    def register_player(self, guild_id: int, player_username: str, player_id: int):
        return self.db.register_player(guild_id=guild_id, player_username=player_username, player_id=player_id)

    def rm_guild_config(self, guild_id: int):
        return self.db.rm_guild_config(guild_id=guild_id)

    def reset(self, guild_id: int):
        return self.db.reset(guild_id=guild_id)

    def get_all(self, guild_id: int):
        return self.db.get_all(guild_id=guild_id)

    def add_canceller_for_guild(self, guild_id: int, canceller):
        return self.db.add_canceller_for_guild(guild_id=guild_id, canceller=canceller)

    def get_cancellers_for_guild(self, guild_id: int):
        return self.db.get_cancellers_for_guild(guild_id=guild_id)

    def is_registered_player(self, guild_id: int, user):
        return self.db.is_registered_player(guild_id=guild_id, player=user)

    def add_decliner_for_guild(self, guild_id: int, user):
        return self.db.add_decliner_for_guild(guild_id=guild_id, decliner=user)

    def get_decliners_for_guild(self, guild_id: int):
        return self.db.get_decliners_for_guild(guild_id=guild_id)

    def rm_attendee_for_guild(self, guild_id: int, user):
        return self.db.rm_attendee_for_guild(guild_id=guild_id, attendee=user)

    def add_attendee_for_guild(self, guild_id: int, user):
        return self.db.add_attendee_for_guild(guild_id=guild_id, attendee=user)

    def rm_decliner_for_guild(self, guild_id: int, user):
        return self.db.rm_decliner_for_guild(guild_id=guild_id, decliner=user)

    def is_player_dm(self, guild_id: int, player_id: int):
        return self.db.is_player_dm(guild_id=guild_id, player_id=player_id)

    def cancel_session(self, guild_id: int):
        return self.db.cancel_session(guild_id=guild_id)

    def get_voice_channel_id(self, server_id: int):
        return self.db.get_voice_channel_id(guild_id=server_id)

    def get_campaign_session_dt(self, server_id: int):
        return self.db.get_campaign_session_dt(guild_id=server_id)
