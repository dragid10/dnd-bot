from app.db.base_db import BaseDB


class Tracker:
    """High-level wrapper around the database layer.
    Uses 'server_id' (the colloquial Discord term) instead of the API's 'guild_id'.
    The underlying BaseDB implementation still uses guild_id internally.
    """

    def __init__(self, db: BaseDB):
        self.db = db
        self.db.connect()

    # ============ Players ============

    def get_players(self, server_id: int):
        """Returns all registered players for the given server."""
        return self.db.get_players_for_guild(server_id)

    def register_player(self, server_id: int, player_username: str, player_id: int):
        """Adds a new player to the server's roster."""
        return self.db.register_player(guild_id=server_id, player_username=player_username, player_id=player_id)

    def unregister_player(self, server_id: int, player):
        """Removes a player from the server's roster."""
        return self.db.unregister_player(guild_id=server_id, player=player)

    def is_registered_player(self, server_id: int, user) -> bool:
        """Checks if a user is registered as a player on the server."""
        return self.db.is_registered_player(guild_id=server_id, player=user)

    def is_player_dm(self, server_id: int, player_id: int) -> bool:
        """Checks if the given player is the DM (game master) for the server."""
        return self.db.is_player_dm(guild_id=server_id, player_id=player_id)

    def get_unanswered_players(self, server_id: int) -> list:
        """Returns players who haven't accepted or declined yet."""
        return self.db.get_unanswered_players(server_id)

    def is_full_group(self, server_id: int) -> bool:
        """Returns True if all registered players have confirmed attendance."""
        return self.db.is_full_group(server_id)

    # ============ Attendees ============

    def get_attendees(self, server_id: int):
        """Returns the list of players who have accepted the upcoming session."""
        return self.db.get_attendees_for_guild(server_id)

    def add_attendee(self, server_id: int, user):
        """Records a player as attending."""
        return self.db.add_attendee_for_guild(guild_id=server_id, attendee=user)

    def rm_attendee(self, server_id: int, user):
        """Removes a player from the attendee list."""
        return self.db.rm_attendee_for_guild(guild_id=server_id, attendee=user)

    # ============ Decliners ============

    def get_decliners(self, server_id: int):
        """Returns the list of players who have declined the upcoming session."""
        return self.db.get_decliners_for_guild(guild_id=server_id)

    def add_decliner(self, server_id: int, user):
        """Records a player as declining."""
        return self.db.add_decliner_for_guild(guild_id=server_id, decliner=user)

    def rm_decliner(self, server_id: int, user):
        """Removes a player from the decliner list."""
        return self.db.rm_decliner_for_guild(guild_id=server_id, decliner=user)

    # ============ Cancellers ============

    def get_cancellers(self, server_id: int):
        """Returns the list of players who have voted to cancel."""
        return self.db.get_cancellers_for_guild(guild_id=server_id)

    def add_canceller(self, server_id: int, canceller):
        """Records a player's vote to cancel."""
        return self.db.add_canceller_for_guild(guild_id=server_id, canceller=canceller)

    # ============ Session State ============

    def get_all(self, server_id: int):
        """Returns a tuple of (attendees, decliners, cancellers) for the server."""
        return self.db.get_all(guild_id=server_id)

    def reset(self, server_id: int):
        """Clears the RSVP lists (attendees, decliners, cancellers) and resets the cancel flag."""
        return self.db.reset(guild_id=server_id)

    def cancel_session(self, server_id: int):
        """Marks the upcoming session as cancelled."""
        return self.db.cancel_session(guild_id=server_id)

    def is_session_cancelled(self, server_id: int) -> bool:
        """Checks whether the upcoming session has been cancelled."""
        return self.db.is_session_cancelled(server_id)

    # ============ Config ============

    def create_server_config(
        self,
        server_id: int,
        voice_channel_id: int,
        dm_username: str,
        dm_id: int,
        session_day: str,
        session_time: str,
        meeting_room: int,
        first_alert: str,
        second_alert: str,
    ):
        """Creates or replaces the bot configuration for a server."""
        self.db.create_guild_config(
            guild_id=server_id,
            voice_channel_id=voice_channel_id,
            dm_username=dm_username,
            dm_id=dm_id,
            session_day=session_day,
            session_time=session_time,
            meeting_room=meeting_room,
            first_alert=first_alert,
            second_alert=second_alert,
        )

    def rm_server_config(self, server_id: int):
        """Deletes the bot configuration for a server."""
        return self.db.rm_guild_config(guild_id=server_id)

    def get_first_alert_configs(self, day_of_week: int) -> list:
        """Returns configs for all servers whose first alert matches the given day."""
        return self.db.get_first_alert_configs(day_of_week)

    def get_second_alert_configs(self, day_of_week: int) -> list:
        """Returns configs for all servers whose second alert matches the given day."""
        return self.db.get_second_alert_configs(day_of_week)

    def get_session_day_configs(self, day_of_week: int):
        """Returns configs for all servers whose session day matches the given day."""
        return self.db.get_session_day_configs(day_of_week)

    def get_voice_channel_id(self, server_id: int) -> int:
        """Returns the configured voice channel ID for the server."""
        return self.db.get_voice_channel_id(guild_id=server_id)

    def get_campaign_session_dt(self, server_id: int):
        """Returns (session_day, session_time) for the server's campaign."""
        return self.db.get_campaign_session_dt(guild_id=server_id)
