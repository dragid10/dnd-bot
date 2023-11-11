import mongoengine

from app import constants, helpers
from app.constants import Collections
from app.db.base_db import BaseDB
from app.model.dao import *
from app.model.dao import _Config


class MongoEngine(BaseDB):
    def connect(self, conn_str: str = None):
        if not conn_str:
            conn_str = constants.db_config.connection_str
        mongoengine.connect(host=conn_str)

    def get_all(self, guild_id: int) -> tuple:
        attendees = self.get_attendees_for_guild(guild_id)
        decliners = self.get_decliners_for_guild(guild_id)
        cancellers = self.get_cancellers_for_guild(guild_id)
        return attendees, decliners, cancellers

    # ============ Players ============
    def _get_players_by_guild_id(self, guild_id: int) -> Players:
        res = Players.objects(guild=guild_id).get()
        return res

    def get_players_for_guild(self, guild_id: int):
        res = self._get_players_by_guild_id(guild_id)
        res = helpers.doc_to_dict(res)
        return res.get(Collections.PLAYERS, [])

    def add_player_for_guild(self, guild_id: int, player: User):
        res: Players = self._get_players_by_guild_id(guild_id)
        res.players.create(name=player.name, id=player.id)
        res.save()

    def rm_player_for_guild(self, guild_id: int, player: User):
        res = self._get_players_by_guild_id(guild_id)
        res.players.filter(id=player.id).delete()
        res.save()

    def register_player(self, guild_id: int, player_username: str, player_id: int):
        new_player = User(name=player_username, id=player_id)
        self.add_player_for_guild(guild_id, new_player)

    def unregister_player(self, guild_id: int, player):
        pass

    def is_full_group(self, guild_id: int) -> bool:
        players = helpers.doc_to_dict(self._get_players_by_guild_id(guild_id).players)
        attendees = helpers.doc_to_dict(
            self._get_attendees_by_guild_id(guild_id).attendees
        )
        # players = self._get_players_by_guild_id(guild_id).players.only(f"{Collections.PLAYERS}.id")
        # attendees = self.__get_attendees_by_guild_id(guild_id).attendees.only(f"{Collections.ATTENDEES}.id")

        # Check if all the players are registered as attendees
        res = all(elem in attendees for elem in players)
        return res

    def is_registered_player(self, guild_id: int, player) -> bool:
        user_id: int = player.id
        res = self._get_players_by_guild_id(guild_id).players.filter(id=user_id).count()
        return res > 0

    def is_player_dm(self, guild_id: int, player_id: int) -> bool:
        res = self._get_config_by_guild_id(guild_id).config
        if not res.session_dm:
            return False
        return res.session_dm.id == player_id

    def get_unanswered_players(self, guild_id: int):
        def transform_user(user_lst: list[dict]):
            ret = {}
            for user in user_lst:
                ret[user["id"]] = user["name"]
            return ret

        players = helpers.doc_to_dict(self._get_players_by_guild_id(guild_id).players)
        attendees = helpers.doc_to_dict(
            self._get_attendees_by_guild_id(guild_id).attendees
        )
        decliners = helpers.doc_to_dict(
            self._get_decliners_by_guild_id(guild_id).decliners
        )

        # Transform list of users into a dictionary of id: name
        players = transform_user(players)
        attendees = transform_user(attendees)
        decliners = transform_user(decliners)

        # Players: {'a', 'b', 'c', 'd'} | Attendees: {'b', 'd'} | Rejections: {'c'}
        # set_players - set_attendees - set_rejections =
        # Result: {'a'}
        # Return the difference of two or more sets as a new set. (i.e. all elements that are in this set but not the others.)
        unanswered = set(players.keys()) - set(attendees.keys()) - set(decliners.keys())

        # Convert set into a list to make it easier to operate with
        unanswered = list(unanswered)

        # If NO ONE has confirmed or declined, then we @ everyone (prompt for response)
        if len(unanswered) == len(players):
            unanswered = ["dnd-players"]
        return unanswered

    def _get_user(self, user: User):
        return helpers.doc_to_dict(user)

    # ============ Attendees ============

    def _get_attendees_by_guild_id(self, guild_id: int) -> Attendees:
        res = Attendees.objects(guild=guild_id).get()
        return res

    def get_attendees_for_guild(self, guild_id: int) -> list[dict]:
        res = self._get_attendees_by_guild_id(guild_id)
        res = helpers.doc_to_dict(res)
        return res.get(Collections.ATTENDEES, [])

    def add_attendee_for_guild(self, guild_id: int, attendee: User):
        # retrieve attendees record
        res: Attendees = self._get_attendees_by_guild_id(guild_id)
        curr_attendees = res.attendees
        curr_attendees.create(name=attendee.name, id=attendee.id)
        res.save()

    def rm_attendee_for_guild(self, guild_id: int, attendee: User):
        res = self._get_attendees_by_guild_id(guild_id)
        res.attendees.filter(id=attendee.id).delete()
        res.save()

    # ============ Decliners ============

    def _get_decliners_by_guild_id(self, guild_id: int) -> Decliners:
        res = Decliners.objects(guild=guild_id).get()
        return res

    def get_decliners_for_guild(self, guild_id: int) -> list[dict]:
        res = self._get_decliners_by_guild_id(guild_id)
        res = helpers.doc_to_dict(res)
        return res.get(Collections.DECLINERS, [])

    def add_decliner_for_guild(self, guild_id: int, decliner):
        res = self._get_decliners_by_guild_id(guild_id)
        res.decliners.create(name=decliner.name, id=decliner.id)
        res.save()

    def rm_decliner_for_guild(self, guild_id: int, decliner):
        res = self._get_decliners_by_guild_id(guild_id)
        res.decliners.filter(id=decliner.id).delete()
        res.save()

    # ============ Cancellers ============

    def _get_cancellers_by_guild_id(self, guild_id: int):
        res = Cancellers.objects(guild=guild_id).get()
        return res

    def get_cancellers_for_guild(self, guild_id: int) -> list[dict]:
        res = self._get_cancellers_by_guild_id(guild_id)
        res = helpers.doc_to_dict(res)
        return res.get(Collections.CANCELLERS, [])

    def add_canceller_for_guild(self, guild_id: int, canceller):
        res = self._get_cancellers_by_guild_id(guild_id)
        res.cancellers.create(name=canceller.name, id=canceller.id)
        res.save()

    def rm_canceller_for_guild(self, guild_id: int, canceller):
        res = self._get_cancellers_by_guild_id(guild_id)
        res.cancellers.filter(id=canceller.id).delete()
        res.save()

    # ============ Config ============

    def _get_config_by_guild_id(self, guild_id: int) -> Config:
        res = Config.objects(guild=guild_id).get()
        return res

    def get_config_for_guild(self, guild_id: int):
        res = self._get_config_by_guild_id(guild_id)
        res = helpers.doc_to_dict(res)
        return res

    def get_gm_for_guild(self, guild_id: int):
        pass

    def _get_session_cancel_flag(self, guild_id: int):
        pass

    def reset(self, guild_id: int):
        self._get_attendees_by_guild_id(guild_id).delete()
        # self._get_attendees_by_guild_id(guild_id).delete().save()
        self._get_decliners_by_guild_id(guild_id).delete()
        # self._get_decliners_by_guild_id(guild_id).delete().save()
        self._get_cancellers_by_guild_id(guild_id).delete()
        # self._get_cancellers_by_guild_id(guild_id).delete().save()
        self.reset_cancel_flag(guild_id)

    def cancel_session(self, guild_id: int) -> bool:
        res = self._get_config_by_guild_id(guild_id)
        res.config.cancel_session = True
        res.save()
        is_cancelled = self._get_config_by_guild_id(guild_id)
        return is_cancelled.config.cancel_session

    def reset_cancel_flag(self, guild_id: int) -> bool:
        guild_config = self._get_config_by_guild_id(guild_id)
        guild_config.config.cancel_session = False
        guild_config.save()
        is_uncancelled = self._get_config_by_guild_id(guild_id)
        return is_uncancelled.config.cancel_session

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
        cancel_session: bool = False,
    ):
        game_master = User(name=dm_username, id=dm_id)
        config_settings = _Config(
            session_dm=game_master,
            vc_id=voice_channel_id,
            session_day=session_day,
            session_time=session_time,
            meeting_room=meeting_room,
            first_alert=first_alert,
            second_alert=second_alert,
        )
        new_config = Config(guild=guild_id, config=config_settings)
        new_config.save(cascade=True)

    def rm_guild_config(self, guild_id: int):
        res = self._get_config_by_guild_id(guild_id)
        res.delete()

    def get_first_alert_configs(self, day_of_the_week: int):
        res_configs = Config.objects(
            config__first_alert=day_of_the_week, config__alerts=True
        )
        res = helpers.doc_to_dict(res_configs)
        return res

    def get_second_alert_configs(self, day_of_the_week: int):
        res_configs = Config.objects(
            config__second_alert=day_of_the_week, config__alerts=True
        ).filter()
        res = helpers.doc_to_dict(res_configs)
        return res

    def get_session_day_configs(self, day_of_the_week: int):
        res_configs = Config.objects(
            config__session_day=day_of_the_week, config__alerts=True
        ).filter()
        res = helpers.doc_to_dict(res_configs)
        return res

    def get_voice_channel_id(self, guild_id: int) -> int:
        res = self._get_config_by_guild_id(guild_id)
        return res.config.vc_id

    def get_campaign_session_dt(self, guild_id: int) -> tuple[int, str]:
        res = self._get_config_by_guild_id(guild_id)
        return res.config.session_day, res.config.session_time

    def is_session_cancelled(self, guild_id: int) -> bool:
        res = self._get_config_by_guild_id(guild_id)
        return res.config.cancel_session
