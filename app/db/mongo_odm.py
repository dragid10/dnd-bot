import mongoengine
from mongoengine.base import BaseList
from more_itertools import locate

from app import constants, helpers
from app.constants import Collections
from app.db.base_db import BaseDB
from app.model.dao import *
from app.model.dao import _Config


class MongoEngine(BaseDB):

    def connect(self):
        mongoengine.connect(host=constants.db_config.connection_str)

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
        res.players.create(player)
        # curr_players: dict[list] = res.players
        # curr_players[Collections.PLAYERS].append(player)
        res.save()

    def rm_player_for_guild(self, guild_id: int, player: User):
        res = self._get_players_by_guild_id(guild_id)
        res.players.filter(id=player.id).delete()
        # res: Players = Players.objects(guild=guild_id, players__id=player.id).get()
        # curr_players: BaseList = res.players
        # rm_index: int = list(locate(curr_players, pred=lambda user: user.id == player.id))[0]
        # del curr_players[rm_index]
        res.save()

    def register_player(self, guild_id: int, dm_username: str, dm_id: int):
        pass

    def unregister_player(self, guild_id: int, player):
        pass

    def is_full_group(self, guild_id: int) -> bool:
        players = helpers.doc_to_dict(self._get_players_by_guild_id(guild_id).players)
        attendees = helpers.doc_to_dict(self.__get_attendees_by_guild_id(guild_id).attendees)
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
        pass

    def get_unanswered_players(self, guild_id: int):
        players = self._get_players_by_guild_id(guild_id).players
        attendees = self.__get_attendees_by_guild_id(guild_id).attendees
        decliners = self._get_decliners_by_guild_id(guild_id).decliners

        # Players: {'a', 'b', 'c', 'd'} | Attendees: {'b', 'd'} | Rejections: {'c'}
        # set_players - set_attendees - set_rejections =
        # Result: {'a'}
        # Return the difference of two or more sets as a new set. (i.e. all elements that are in this set but not the others.)
        unanswered = set(players.objects.id) - set(attendees.objects.id) - set(decliners.objects.id)

        # Convert set into a list to make it easier to operate with
        unanswered = list(unanswered)
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
        res = self.__get_attendees_by_guild_id(guild_id)
        res = helpers.doc_to_dict(res)
        return res.get(Collections.ATTENDEES, [])

    def add_attendee_for_guild(self, guild_id: int, attendee: User):
        # retrieve attendees record
        res: Attendees = self.__get_attendees_by_guild_id(guild_id)
        curr_attendees: dict[list] = res.attendees
        curr_attendees[Collections.ATTENDEES].append(attendee)
        res.save()

    def rm_attendee_for_guild(self, guild_id: int, attendee: User):
        res: Attendees = Attendees.objects(guild=guild_id, attendees__id=attendee.id).get()
        curr_attendees: BaseList = res.attendees
        rm_index: int = list(locate(curr_attendees, pred=lambda user: user.id == attendee.id))[0]
        del curr_attendees[rm_index]
        res.save()

    # ============ Decliners ============

    def _get_decliners_by_guild_id(self, guild_id: int) -> Decliners:
        res = Decliners.objects(guild=guild_id).get()
        return res

    def get_decliners_for_guild(self, guild_id: int) -> list[dict]:
        res = Decliners.objects(guild=guild_id).get()
        res = helpers.doc_to_dict(res)
        return res.get(Collections.DECLINERS, [])

    def add_decliner_for_guild(self, guild_id: int, decliner):
        res = self._get_decliners_by_guild_id(guild_id)
        res.decliners.create(User.from_discord_author(decliner))
        res.save()

    def rm_decliner_for_guild(self, guild_id: int, decliner):
        pass

    # ============ Cancellers ============

    def _get_cancellers_by_guild_id(self, guild_id: int):
        res = Cancellers.objects(guild=guild_id).get()
        return res

    def get_cancellers_for_guild(self, guild_id: int) -> list[dict]:
        res = self._get_cancellers_by_guild_id(guild_id)
        res = helpers.doc_to_dict(res)
        return res

    def add_canceller_for_guild(self, guild_id: int, canceller):
        res = self._get_cancellers_by_guild_id(guild_id)
        res.cancellers.create(User.from_discord_author(canceller))
        res.save()

    def rm_canceller_for_guild(self, guild_id: int, canceller):
        pass

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
        self._get_attendees_by_guild_id(guild_id).delete().save()
        self._get_decliners_by_guild_id(guild_id).delete().save()
        self._get_cancellers_by_guild_id(guild_id).delete().save()
        self.reset_cancel_flag(guild_id)

    def skip(self, guild_id: int):
        res = self._get_config_by_guild_id(guild_id)
        res.config.skip = True
        res.save()

    def cancel_session(self, guild_id: int) -> bool:
        pass

    def reset_cancel_flag(self, guild_id: int) -> bool:
        guild_config = self._get_config_by_guild_id(guild_id)
        guild_config.config.cancel_session = False
        guild_config.save()
        return True

    def create_guild_config(self, guild_id: int, voice_channel_id: int, dm_username: str, dm_id: int, session_day: str, session_time: str,
                            meeting_room: int,
                            first_alert: str, second_alert: str, cancel_session: bool = False):
        game_master = User(name=dm_username, id=dm_id)
        config_settings = _Config(session_dm=game_master,
                                  vc_id=voice_channel_id,
                                  session_day=session_day,
                                  session_time=session_time,
                                  meeting_room=meeting_room,
                                  first_alert=first_alert,
                                  second_alert=second_alert)
        new_config = Config(guild=guild_id,
                            config=config_settings
                            )
        new_config.save(cascade=True)

    def rm_guild_config(self, guild_id: int):
        res = self._get_config_by_guild_id(guild_id)
        res.delete()
        res.save()

    def get_first_alert_configs(self, day_of_the_week: int):
        res_configs = Config.objects(config__first_alert=day_of_the_week, config__alerts=True)
        res = helpers.doc_to_dict(res_configs)
        return res

    def get_second_alert_configs(self, day_of_the_week: int):
        res_configs = Config.objects(config__second_alert=day_of_the_week, config__alerts=True).filter()
        res = helpers.doc_to_dict(res_configs)
        return res

    def get_session_day_configs(self, day_of_the_week: int):
        res_configs = Config.objects(config__session_day=day_of_the_week, config__alerts=True).filter()
        res = helpers.doc_to_dict(res_configs)
        return res

    def get_voice_channel_id(self, guild_id: int) -> int:
        pass

    def get_campaign_session_dt(self, guild_id: int) -> tuple[str, str]:
        pass

    def is_session_cancelled(self, guild_id: int) -> bool:
        res = self._get_config_by_guild_id(guild_id)
        return res.config.cancel_session
