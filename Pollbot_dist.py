import sys
import json
import telepot
from telepot.delegate import pave_event_space, per_chat_id, create_open, include_callback_query_chat_id
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

sondaggi = {}
with open('groups.json', 'r') as f:
	groups = json.load(f)

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
    global groups
    def __init__(self, *args, **kwargs):
        super(MessageCounter, self).__init__(*args, **kwargs)
        self._count = 0
        self._poll_of_the_day = None
        self._markup = None

    def poll(self, msg, chat_id, chat_type, from_id):

        if chat_type == 'group' or chat_type == 'supergroup':
            try:
                message_with_inline_keyboard = self.sender.sendMessage(poll_of_the_day, reply_markup=markup) if (from_id == int(Master)) else self.sender.sendMessage('Only the Great Master of the Council can hold a poll')
            except telepot.exception.TelegramError:
                self.sender.sendMessage('No poll set')
        elif chat_type == 'private':
            lista = msg['text'].split('&@')
            self._poll_of_the_day = lista[0][6:]
            del lista[0]
            risultati = {}	

            buttons = []
            for e in lista:
                risultati[e] = 0
                buttons.append([InlineKeyboardButton(text=str(e) + ' (' + str(risultati[e]) + ')', callback_data=e)])
            self._markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            bot.sendMessage(chat_id, 'Poll set')

    def dest(self, msg, chat_type, from_id):
        buttons = []
        for e in groups.keys():
            buttons.append([InlineKeyboardButton(text=e, callback_data=str(groups[e]))])
        contacts = InlineKeyboardMarkup(inline_keyboard=buttons)
        self.sender.sendMessage('Whom have you created this poll for?', reply_markup=contacts)

    def on_callback_query(self, msg):
        print(msg)
        global sondaggi
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        sondaggi[data, from_id] = [self._poll_of_the_day, self._markup]
        self.bot.answerCallbackQuery(query_id, text='All set')
        self.sender.sendMessage('All set')

    def on_chat_message(self, msg):
        chatter(msg)
        print(msg)
        content_type, chat_type, chat_id = telepot.glance(msg)
        from_id = msg['from']['id']
        if content_type == 'group_chat_created' or content_type == 'supergroup_chat_created':
            groups[msg['chat']['title']] = [chat_id, from_id]
            with open('groups.json', 'w') as json_file:
                json.dump(groups, json_file, sort_keys=True, indent=4, separators=(',', ': '))
        text = msg['text'].replace(bot_name, '')
        if text[:5] == '/poll':
            self.poll(msg, chat_id, chat_type, from_id)
        elif text == '/dest':
            self.dest(msg, chat_type, from_id)

TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(pave_event_space())(
        per_chat_id(), create_open, MessageCounter, timeout=86400),
])
bot_name = '@' + bot.getMe()['username']
bot.message_loop(run_forever='Listening ...')
