import pytest

from directorofme_auth.models import SlackBot

@pytest.fixture
def slack_token_body():
    return {
        'ok': True,
        'user_id': 'UAUUYSM0U',
        'team_name': 'DirectorOf.Me',
        'access_token': 'xoxp-358888692659-368984905028-371796726161-4bed5ff36950b4b717933b71c28f49ab',
        'response_metadata': { 'warnings': ['superfluous_charset'] },
        'bot': {
            'bot_user_id': 'UAJU34QQ3',
            'bot_access_token': 'xoxb-358955160819-9v42rM8d9rH4FYKO5ZcYES8B'
        },
        'warning': 'superfluous_charset',
        'scope': [ 'identify,bot,commands,incoming-webhook,dnd:read,chat:write:bot,dnd:write,'\
                   'identity.basic,identity.email' ],
        'team_id': 'TAJS4LCKD'
    }
