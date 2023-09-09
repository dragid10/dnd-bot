import abc
from abc import abstractmethod


class BaseDB(metaclass=abc.ABCMeta):

    @abstractmethod
    def connect(self, conn_str: str = None):
        pass

    @abstractmethod
    def _get_user(self, user):
        pass

    @abstractmethod
    def get_all(self, guild_id: int):
        pass

    # ============ Attendees ============
    @abstractmethod
    def get_attendees_for_guild(self, guild_id: int) -> list[dict]:
        pass

    @abstractmethod
    def add_attendee_for_guild(self, guild_id: int, attendee):
        pass

    @abstractmethod
    def rm_attendee_for_guild(self, guild_id: int, attendee):
        pass

    @abstractmethod
    def get_decliners_for_guild(self, guild_id: int) -> list[dict]:
        pass

    @abstractmethod
    def get_cancellers_for_guild(self, guild_id: int) -> list[dict]:
        pass

    @abstractmethod
    def get_config_for_guild(self, guild_id: int):
        pass

    @abstractmethod
    def get_players_for_guild(self, guild_id: int) -> list[dict]:
        pass

    @abstractmethod
    def get_gm_for_guild(self, guild_id: int):
        pass

    @abstractmethod
    def _get_session_cancel_flag(self, guild_id: int):
        pass

    @abstractmethod
    def reset(self, guild_id: int):
        pass

    @abstractmethod
    def cancel_session(self, guild_id: int) -> bool:
        pass

    @abstractmethod
    def reset_cancel_flag(self, guild_id: int) -> bool:
        pass

    @abstractmethod
    def add_decliner_for_guild(self, guild_id: int, decliner):
        pass

    @abstractmethod
    def rm_decliner_for_guild(self, guild_id: int, decliner):
        pass

    @abstractmethod
    def add_canceller_for_guild(self, guild_id: int, canceller):
        pass

    @abstractmethod
    def rm_canceller_for_guild(self, guild_id: int, canceller):
        pass

    @abstractmethod
    def add_player_for_guild(self, guild_id: int, player):
        pass

    @abstractmethod
    def rm_player_for_guild(self, guild_id: int, player):
        pass

    @abstractmethod
    def create_guild_config(
            self,
            guild_id: int,
            voice_channel_id: int,
            dm_username: str,
            dm_id: int,
            session_day: str,
            session_time: str,
            meeting_room: int,
            first_alert: str,
            second_alert: str,
            cancel_session: bool = False
    ):
        pass

    @abstractmethod
    def rm_guild_config(self, guild_id: int):
        pass

    @abstractmethod
    def get_first_alert_configs(self, day_of_the_week: int):
        pass

    @abstractmethod
    def get_second_alert_configs(self, day_of_the_week: int):
        pass

    @abstractmethod
    def get_session_day_configs(self, day_of_the_week: int):
        pass

    @abstractmethod
    def get_voice_channel_id(self, guild_id: int) -> int:
        pass

    @abstractmethod
    def get_campaign_session_dt(self, guild_id: int) -> tuple[str, str]:
        pass

    @abstractmethod
    def register_player(self, guild_id: int, player_username: str, player_id: int):
        pass

    @abstractmethod
    def unregister_player(self, guild_id: int, player):
        pass

    @abstractmethod
    def \
            is_full_group(self, guild_id: int) -> bool:
        pass

    @abstractmethod
    def is_registered_player(self, guild_id: int, player) -> bool:
        pass

    @abstractmethod
    def is_player_dm(self, guild_id: int, player_id: int) -> bool:
        pass

    @abstractmethod
    def is_session_cancelled(self, guild_id: int) -> bool:
        pass

    @abstractmethod
    def get_unanswered_players(self, guild_id: int):
        pass
