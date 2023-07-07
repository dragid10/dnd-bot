from mongoengine import BooleanField, Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, IntField, LongField, \
    StringField


# +++++++++++++ Embedded Documents +++++++++++++
class User(EmbeddedDocument):
    name = StringField(required=True)
    id = LongField(required=True)

    @staticmethod
    def from_discord_author(author):
        return User(name=author.name, id=author.id)


class _Config(EmbeddedDocument):
    session_dm = EmbeddedDocumentField(db_field="session-dm", document_type=User)
    vc_id = LongField(db_field="vc-id", required=True)
    session_day = IntField(db_field="session-day", required=True)
    session_time = StringField(db_field="session-time", required=True)
    meeting_room = LongField(db_field="meeting-room", required=True)
    first_alert = IntField(db_field="first-alert", required=True)
    second_alert = IntField(db_field="second-alert", required=True)
    alerts = BooleanField(required=True, default=True)
    cancel_session = BooleanField(db_field="cancel-session", required=True, default=False)


# +++++++++++++ Collection Documents +++++++++++++
class Players(Document):
    guild = LongField(required=True)
    players = EmbeddedDocumentListField(User)


class Config(Document):
    guild = LongField(required=True)
    config = EmbeddedDocumentField(_Config)


class Attendees(Document):
    guild = LongField(required=True)
    attendees = EmbeddedDocumentListField(User)


class Cancellers(Document):
    guild = LongField(required=True)
    cancellers = EmbeddedDocumentListField(User)


class Decliners(Document):
    guild = LongField(required=True)
    decliners = EmbeddedDocumentListField(User)


y
