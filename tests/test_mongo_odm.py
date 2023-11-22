import mongoengine
import mongomock
import pytest
from mongoengine import DoesNotExist

from app.db.mongo_odm import MongoEngine
from app.model.dao import (
    Attendees,
    Cancellers,
    Config,
    Decliners,
    Players,
    User,
    _Config,
)


def seed_database():
    player = User(name="test", id=123)
    Players(guild=123, players=[player]).save()
    Decliners(guild=123, decliners=[player]).save()
    Attendees(guild=123, attendees=[player]).save()
    Cancellers(guild=123, cancellers=[player]).save()
    Config(
        guild=123,
        config=_Config(
            session_dm=player,
            vc_id=1123,
            session_day=2,
            session_time="11:00",
            meeting_room=1234567889,
            first_alert=9,
            second_alert=10,
            cancel_session=False,
        ),
    ).save()


class TestMongoEngine:
    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(self):
        """Fixture to execute asserts before and after a test is run"""
        # Setup: fill with any logic you want
        mongoengine.connect(
            db="mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
        )
        self.db: MongoEngine = MongoEngine()
        seed_database()
        yield  # this is where the testing happens

        # Teardown : fill with any logic you want
        mongoengine.disconnect()

    @pytest.fixture
    def test_player(self):
        return User(name="test", id=123)

    @pytest.fixture
    def test_player2(self):
        return User(name="test2", id=456)

    @pytest.fixture
    def test_guild_id(self):
        return 123

    def test_connect(self):
        conn = mongoengine.get_connection()
        assert conn is not None

    def test_get_all(self, test_guild_id):
        expected = 3
        res = self.db.get_all(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected

    def test__get_players_by_guild_id(self, test_player, test_guild_id):
        expected = test_player.name
        res = self.db._get_players_by_guild_id(guild_id=test_guild_id)
        actual = res.players[0].name
        assert actual == expected

    def test_get_players_for_guild(self, test_guild_id):
        expected = 1
        res = self.db.get_players_for_guild(guild_id=123)
        actual = len(res)
        assert actual == expected

    def test_add_player_for_guild(self, test_player2, test_guild_id):
        expected = 2
        self.db.add_player_for_guild(guild_id=123, player=test_player2)
        res = Players.objects(guild=test_guild_id).get().players
        actual = len(res)
        assert actual == expected

    def test_rm_player_for_guild(self, test_player, test_guild_id):
        expected = 0
        self.db.rm_player_for_guild(guild_id=123, player=test_player)
        res = Players.objects(guild=test_guild_id).get().players
        actual = len(res)
        assert actual == expected

    def test_register_player(self, test_player2, test_guild_id):
        expected = 2
        self.db.register_player(
            guild_id=test_guild_id,
            player_username=test_player2.name,
            player_id=test_player2.id,
        )
        res = Players.objects(guild=test_guild_id).get().players
        actual = len(res)
        assert actual == expected

    def test_is_full_group(self, test_guild_id):
        assert self.db.is_full_group(guild_id=test_guild_id) is True

    def test_is_not_full_group(self, test_player2, test_guild_id):
        self.db.add_player_for_guild(guild_id=test_guild_id, player=test_player2)
        assert self.db.is_full_group(guild_id=test_guild_id) is False

    def test_is_registered_player(self, test_player, test_guild_id):
        assert self.db.is_registered_player(guild_id=test_guild_id, player=test_player) is True

    def test_is_player_dm(self, test_player, test_guild_id):
        assert self.db.is_player_dm(guild_id=test_guild_id, player_id=test_player.id) is True

    def test_get_unanswered_players_none(self, test_guild_id):
        expected = list()
        actual = self.db.get_unanswered_players(guild_id=test_guild_id)
        assert actual == expected

    def test_get_unanswered_players_1ormore(self, test_guild_id, test_player2):
        expected = 1
        self.db.add_player_for_guild(guild_id=test_guild_id, player=test_player2)
        actual = self.db.get_unanswered_players(guild_id=test_guild_id)
        assert len(actual) == expected
        assert actual == [test_player2.id]

    def test__get_user(self, test_player):
        expected = test_player.name
        actual = self.db._get_user(user=test_player)["name"]
        assert actual == expected

    def test__get_attendees_by_guild_id(self, test_guild_id, test_player):
        expected = 1
        res = self.db._get_attendees_by_guild_id(guild_id=test_guild_id)
        actual = len(res.attendees)
        assert actual == expected
        assert res.attendees[0].name == test_player.name

    def test_get_attendees_for_guild(self, test_guild_id, test_player):
        expected = 1
        res = self.db.get_attendees_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected
        assert res[0]["name"] == test_player.name

    def test_add_attendee_for_guild(self, test_guild_id, test_player2):
        expected = 2
        self.db.add_player_for_guild(guild_id=test_guild_id, player=test_player2)
        self.db.add_attendee_for_guild(guild_id=test_guild_id, attendee=test_player2)
        res = self.db.get_attendees_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected
        assert res[1]["name"] == test_player2.name

    def test_rm_attendee_for_guild(self, test_guild_id, test_player):
        expected = 0
        self.db.rm_attendee_for_guild(guild_id=test_guild_id, attendee=test_player)
        res = self.db.get_attendees_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected

    def test__get_decliners_by_guild_id(self, test_guild_id, test_player):
        expected = 1
        res = self.db._get_decliners_by_guild_id(guild_id=test_guild_id)
        actual = len(res.decliners)
        assert actual == expected
        assert res.decliners[0].name == test_player.name

    def test_get_decliners_for_guild(self, test_guild_id, test_player):
        expected = 1
        res = self.db.get_decliners_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected
        assert res[0]["name"] == test_player.name

    def test_add_decliner_for_guild(self, test_guild_id, test_player2):
        expected = 2
        self.db.add_player_for_guild(guild_id=test_guild_id, player=test_player2)
        self.db.add_decliner_for_guild(guild_id=test_guild_id, decliner=test_player2)
        res = self.db.get_decliners_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected
        assert res[1]["name"] == test_player2.name

    def test_rm_decliner_for_guild(self, test_guild_id, test_player):
        expected = 0
        self.db.rm_decliner_for_guild(guild_id=test_guild_id, decliner=test_player)
        res = self.db.get_decliners_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected

    def test__get_cancellers_by_guild_id(self, test_guild_id, test_player):
        expected = 1
        res = self.db._get_cancellers_by_guild_id(guild_id=test_guild_id)
        actual = len(res.cancellers)
        assert actual == expected
        assert res.cancellers[0].name == test_player.name

    def test_get_cancellers_for_guild(self, test_guild_id, test_player):
        expected = 1
        res = self.db.get_cancellers_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected
        assert res[0]["name"] == test_player.name

    def test_add_canceller_for_guild(self, test_guild_id, test_player2):
        expected = 2
        self.db.add_player_for_guild(guild_id=test_guild_id, player=test_player2)
        self.db.add_canceller_for_guild(guild_id=test_guild_id, canceller=test_player2)
        res = self.db.get_cancellers_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected
        assert res[1]["name"] == test_player2.name

    def test_rm_canceller_for_guild(self, test_guild_id, test_player):
        expected = 0
        self.db.rm_canceller_for_guild(guild_id=test_guild_id, canceller=test_player)
        res = self.db.get_cancellers_for_guild(guild_id=test_guild_id)
        actual = len(res)
        assert actual == expected

    def test__get_config_by_guild_id(self, test_guild_id, test_player):
        expected = 1123
        res = self.db._get_config_by_guild_id(guild_id=test_guild_id)
        actual = res.config.vc_id
        assert actual == expected

    def test_get_config_for_guild(self, test_guild_id):
        expected = 1123
        res = self.db.get_config_for_guild(guild_id=test_guild_id)
        actual = res.get("config").get("vc-id")
        assert actual == expected

    def test_get_gm_for_guild(self, test_guild_id):
        expected = "test"
        res = self.db.get_config_for_guild(guild_id=test_guild_id)
        actual = res.get("config").get("session-dm").get("name")
        assert actual == expected

    def test__get_session_cancel_flag(self, test_guild_id):
        expected = False
        res = self.db.get_config_for_guild(guild_id=test_guild_id)
        actual = res.get("config").get("cancel-session")
        assert actual == expected

    def test_reset(self, test_guild_id):
        original_cancellers = self.db.get_cancellers_for_guild(guild_id=test_guild_id)
        assert len(original_cancellers) == 1
        self.db.reset(guild_id=test_guild_id)
        with pytest.raises(DoesNotExist):
            self.db.get_cancellers_for_guild(guild_id=test_guild_id)

    def test_cancel_session(self, test_guild_id):
        expected = True
        actual = self.db.cancel_session(guild_id=test_guild_id)
        assert expected == actual

    def test_reset_cancel_flag(self, test_guild_id):
        expected = False
        actual = self.db.reset_cancel_flag(guild_id=test_guild_id)
        assert expected == actual

    def test_create_guild_config(self, test_player):
        expected = 442211
        guild_id = 789
        self.db.create_guild_config(
            guild_id=guild_id,
            voice_channel_id=442211,
            dm_username=test_player.name,
            dm_id=test_player.id,
            session_day="4",
            session_time="11:00",
            meeting_room=1234567889,
            first_alert="9",
            second_alert="10",
        )
        res = self.db.get_config_for_guild(guild_id=guild_id)
        actual = res.get("config").get("vc-id")
        assert expected == actual

    def test_rm_guild_config(self, test_guild_id):
        self.db.rm_guild_config(guild_id=test_guild_id)
        with pytest.raises(DoesNotExist):
            self.db.get_config_for_guild(guild_id=test_guild_id)

    def test_get_first_alert_configs(self, test_guild_id):
        expected = 9
        res = self.db.get_first_alert_configs(day_of_the_week=expected)[0]
        actual = res.get("config").get("first-alert")
        assert expected == actual

    def test_get_second_alert_configs(self):
        expected = 10
        res = self.db.get_second_alert_configs(day_of_the_week=expected)[0]
        actual = res.get("config").get("second-alert")
        assert expected == actual

    def test_get_session_day_configs(self):
        expected = 2
        res = self.db.get_session_day_configs(day_of_the_week=expected)[0]
        actual = res.get("config").get("session-day")
        assert expected == actual

    def test_get_voice_channel_id(self, test_guild_id):
        expected = 1123
        res = self.db.get_voice_channel_id(guild_id=test_guild_id)
        actual = res
        assert actual == expected

    def test_get_campaign_session_dt(self, test_guild_id):
        expected = (2, "11:00")
        res = self.db.get_campaign_session_dt(guild_id=test_guild_id)
        actual = res
        assert actual == expected

    def test_is_session_cancelled(self, test_guild_id):
        expected = False
        res = self.db.is_session_cancelled(guild_id=test_guild_id)
        actual = res
        assert actual == expected

    @pytest.fixture(autouse=True)
    def teardown(self):
        mongoengine.disconnect(alias="testdb")
