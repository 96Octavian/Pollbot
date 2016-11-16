import sys
import telepot
from telepot.delegate import pave_event_space, per_chat_id, create_open

#Record everyone that writes to your bot
def chatter(msg):
    first_name = msg['from']['first_name']
    from_id = msg['from']['id']
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
        if msg['from']['username']:
            user_name = msg['from']['username']
            if chat_type == 'private':
                person = user_name + ': ' + str(from_id)
            elif chat_type == 'group' or chat_type == 'supergroup':
                group_name = msg['chat']['title']
                person = user_name + ': ' + str(from_id) + ' @ ' + group_name + ', ' + str(chat_id)
    except KeyError:
        if chat_type == 'private':
            person = 'No username - ' + str(first_name) + ': ' + str(from_id)
        elif chat_type == 'group' or chat_type == 'supergroup':
            group_name = msg['chat']['title']
            person = 'No username - ' + str(first_name) + ': ' + str(from_id) + ' @ ' + group_name + ', ' + str(chat_id)
    with open("./contatti.txt", "a") as myfile:
        myfile.write(person + '\n')

class MessageCounter(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(MessageCounter, self).__init__(*args, **kwargs)
        chatter(msg)
        self._count = 0

    def on_chat_message(self, msg):
        self._count += 1
        self.sender.sendMessage(self._count)

TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, MessageCounter, timeout=86400),
])
bot.message_loop(run_forever='Listening ...')