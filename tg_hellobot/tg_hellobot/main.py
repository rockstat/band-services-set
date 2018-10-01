from band import expose, settings

"""
Useful links:
https://habr.com/post/322078/
"""

set_wh_url = f"https://api.telegram.org/bot{settings.token}/sendMessage"

@expose.handler()
async def send(data,**params):
    pass

@expose.handler()
async def main(data, **params):
    if 'message' in data and 'new_chat_member' in data['message']:
        member = data['message']['new_chat_member']
        chat = data['message']['chat']
        name = member['username'] and '@' + \
            member['username'] or member['first_name']

        return {
            'method': 'sendMessage',
            'chat_id': chat['id'],
            'text': 'Привет, {}!\nРасскажи немного о себе с хештегом #me.'.format(name)
        }
    return {}
