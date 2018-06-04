from base64 import b64encode, b64decode

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.types import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from directorofme.crypto import RSACipher
from directorofme.authorization import groups as group_module
from . import Profile, db

class SlackBot(db.Model):
    """
    Slack is a model for storing team-level bot information so that bots can be
    shared across users and the sign-up process can be streamlined for all but
    the first installing user.
    """
    __tablename__ = "slack_bot"

    #: user who installed this bot to slack
    installing_slack_user_id = Column(String(25), nullable=False)

    #: profile id of installing user
    installing_profile_id = Column(UUIDType, ForeignKey(Profile.id), nullable=False)

    #: profile of installing user
    installing_profile = relationship(Profile)

    #: team who this bot is for in slack
    team_id = Column(String(25), unique=True, nullable=False, index=True)

    #: bot user id
    bot_id = Column(String(25), unique=True, nullable=False)

    #: aaccess token for the bot, encrypted
    encrypted_access_token = Column(String(4096), nullable=False)

    #: scopes for this slack bot
    scopes = Column(ARRAY(String(25)), nullable=False)

    def __init__(self, *args, public_key=None, private_key=None, access_token=None, **kwargs):
        super().__init__(*args, **kwargs)

        # override any passed or default perms, this object is system only use
        self.read = (group_module.root.name,)
        self.write = (group_module.root.name,)
        self.delete = (group_module.root.name,)

        self.cipher = RSACipher(public_key, private_key)
        self.access_token = access_token

    @property
    def access_token(self):
        return self.cipher.decrypt(self.encrypted_access_token)

    @access_token.setter
    def access_token(self, val):
        if val is None:
            self.encrypted_access_token = None
        self.encrypted_access_token = self.cipher.encrypt(val)
