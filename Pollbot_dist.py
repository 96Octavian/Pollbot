import sys
import json
import telepot
import logging
import argparse
from telepot.delegate import pave_event_space, per_chat_id, create_open, include_callback_query_chat_id
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

"""
Python 3.5.2
A Python bot for casting polls: the users who adds the bot to a group acts as the administrator and
is the only one capable of starting and stopping polls
"""

totalitario = {}
sondaggi = {}
with open('groups.json', 'r') as f:
	groups = json.load(f)

# Deafults
LOG_FILENAME = './Pollbot.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s')

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="My simple Python Telegram bot")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")
parser.add_argument("-T", "--TOKEN", help="bot TOKEN identifier")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
    LOG_FILENAME = args.log
if args.TOKEN:
    TOKEN = args.TOKEN
else:
    logging.error('No TOKEN specified')
    print("You must specify the bot's TOKEN")
    sys.exit(0)

logger = logging.getLogger(__name__)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
    def __init__(self, logger, level):
        #Needs a logger and a logger level.
        self.logger = logger
        self.level = level

    def write(self, message):
        # Only log if there is a message (not just a new line)
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
#sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

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

#Per-chat class handler: every chat has its own variable space and keeps track of its poll
class MessageCounter(telepot.helper.ChatHandler):
    global groups
    def __init__(self, *args, **kwargs):
        super(MessageCounter, self).__init__(*args, **kwargs)
        self._poll_of_the_day = None
        self._markup = None
        self._message_with_inline_keyboard = None
        self._risultati = {}
        self._votanti = {}
        self._msg_idf = None
        self._owner = None

    def exitpoll(self, msg, chat_id, from_id, chat_type):
        if self._owner == None:
            self.sender.sendMessage('No ongoing poll')
        elif (chat_type == 'group' or chat_type == 'supergroup') and from_id == self._owner:
            try:
                exit_poll = self._poll_of_the_day + '\n'
                for e in self._risultati.keys():
                    exit_poll += e + ': ' + str(self._risultati[e]) + '\n'
                self.sender.sendMessage(exit_poll)
                self._poll_of_the_day = None
                self._risultati = {}
                self._markup = None
                self._votanti = {}
                self._message_with_inline_keyboard = None
                logging.info('Poll closed in group %s', msg['chat']['title'])
            except TypeError:
                self.sender.sendMessage('No ongoing poll')
        elif (chat_type == 'group' or chat_type == 'supergroup') and from_id != self._owner:
            self.sender.sendMessage('Only the Great Master can put an end to an ongoing poll')
        elif chat_type == 'private':
            self.sender.sendMessage('You need to be in a group to stop a poll')


    def ongoing():
        if chat_type == 'group' or chat_type == 'supergroup':
            try:
                self._message_with_inline_keyboard = self.sender.sendMessage(self._poll_of_the_day, reply_markup=sondaggi[(str(chat_id), from_id)][1])
            except telepot.exception.TelegramError:
                self.sender.sendMessage('No poll set')
        else:
            self.sender.sendMessage('There cannot be polls outside groups')


    def dest(self, msg, chat_type, from_id):
        if chat_type == 'private':
            buttons = []
            element = [x for x in groups.keys() if groups[x][1] == from_id]
            for e in element:
                buttons.append([InlineKeyboardButton(text=e, callback_data=str(groups[e][0]))])
            contacts = InlineKeyboardMarkup(inline_keyboard=buttons)
            self.sender.sendMessage('Who have you created this poll for?', reply_markup=contacts) if len(element) != 0 else self.sender.sendMessage('You have to add me to a group first')
        else:
            self.sender.sendMessage('Polls destination have to be voted in the Great High Council')


    def poll(self, msg, chat_id, chat_type, from_id):

        if chat_type == 'group' or chat_type == 'supergroup':
            global sondaggi
            try:
                if (str(chat_id), from_id) in sondaggi.keys():
                    self._owner = from_id
                    self._poll_of_the_day = sondaggi[(str(chat_id), from_id)][0]
                    self._message_with_inline_keyboard = self.sender.sendMessage(self._poll_of_the_day, reply_markup=sondaggi[(str(chat_id), from_id)][1])
                    self._risultati = totalitario[str(chat_id)]
                    del totalitario[str(chat_id)]
                    logging.info('Poll started in group %s', msg['chat']['title'])
                else:
                    self.sender.sendMessage('Only the Great Master of the Council can hold a poll')
            except telepot.exception.TelegramError:
                self.sender.sendMessage('No poll set')
        elif chat_type == 'private':
            lista = msg['text'].split(' . ')
            if len(lista) == 1:
                self.sender.sendMessage('No choices specified: poll not set')
                logging.info('Wrong request syntax')
            elif len(lista) > 1:
                self._poll_of_the_day = lista[0][6:]
                del lista[0]
                self._risultati = {}
#                logging.info('Poll set: %s', self._poll_of_the_day, lista)
                logging.info('Poll set')

                buttons = []
                for e in lista:
                    self._risultati[e] = 0
                    buttons.append([InlineKeyboardButton(text=e + ' (' + str(self._risultati[e]) + ')', callback_data=e)])
                self._markup = InlineKeyboardMarkup(inline_keyboard=buttons)
                self.sender.sendMessage('Poll set, only one choice possible') if len(lista) == 1 else self.sender.sendMessage('Poll set')
            
                
    def scrutatore(self, msg, data, from_id, query_id):
        try:
            if from_id not in self._votanti.keys():
                logging.info('One vote from group')
                self._risultati[data] += 1
                self._votanti[from_id] = data
                bot.answerCallbackQuery(query_id, text=data + ': ' + str(self._risultati[data]))
                buttons = []
                for e in self._risultati.keys():
                    buttons.append([InlineKeyboardButton(text=str(e) + ' (' + str(self._risultati[e]) + ')', callback_data=e)])
                self._markup = InlineKeyboardMarkup(inline_keyboard=buttons)
                self._msg_idf = telepot.message_identifier(self._message_with_inline_keyboard)
#                print(self._poll_of_the_day)
                bot.editMessageText(self._msg_idf, self._poll_of_the_day, reply_markup=self._markup)
            else:
                if self._votanti[from_id] == data:
                    bot.answerCallbackQuery(query_id, text=msg['from']['username'] + ' has already cast his vote')
                else:
                    logging.info('One vote from group')
                    self._risultati[data] += 1
                    self._risultati[self._votanti[from_id]] -= 1
                    self._votanti[from_id] = data
                    bot.answerCallbackQuery(query_id, text=data + ': ' + str(self._risultati[data]))
                    buttons = []
                    for e in self._risultati.keys():
                        buttons.append([InlineKeyboardButton(text=str(e) + ' (' + str(self._risultati[e]) + ')', callback_data=e)])
                    self._markup = InlineKeyboardMarkup(inline_keyboard=buttons)
                    self._msg_idf = telepot.message_identifier(self._message_with_inline_keyboard)
                    bot.editMessageText(self._msg_idf, self._poll_of_the_day, reply_markup=self._markup)
        except ValueError:
            bot.answerCallbackQuery(query_id, text='Poll closed')


    def on_callback_query(self, msg):
        global sondaggi
        global totalitario

        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        try:
            if int(data) < 0:
                totalitario[str(data)] = self._risultati
                sondaggi[data, from_id] = [self._poll_of_the_day, self._markup]
                logging.info('Destination chosen: %s', str(data))
                self.bot.answerCallbackQuery(query_id, text='All set')
                self.sender.sendMessage('All set')
            else:
                self.scrutatore(msg, data, from_id, query_id)
        except ValueError:
            self.scrutatore(msg, data, from_id, query_id)

            
    def on_chat_message(self, msg):
        global groups
        chatter(msg)
        content_type, chat_type, chat_id = telepot.glance(msg)
        from_id = msg['from']['id']
        logging.info('Message content: %s', content_type)
        logging.info('Chat type: %s', chat_type)
        if content_type == 'new_chat_member':
            groups[msg['chat']['title']] = [chat_id, from_id]
            with open('groups.json', 'w') as json_file:
                json.dump(groups, json_file, sort_keys=True, indent=4, separators=(',', ': '))
            logging.info('Added to %s', msg['chat']['title'])
        elif content_type == 'left_chat_member' and msg['left_chat_participant']['id'] == 287100649:
            del groups[msg['chat']['title']]
            with open('groups.json', 'w') as json_file:
                json.dump(groups, json_file, sort_keys=True, indent=4, separators=(',', ': '))
            logging.info('Removed from %s', msg['chat']['title'])
        else:
            text = msg['text'].replace(bot_name, '')
            logging.info('Text: %s', text)
            if text[:5] == '/poll':
                self.poll(msg, chat_id, chat_type, from_id)
            elif text == '/dest':
                self.dest(msg, chat_type, from_id)
            elif text == '/exitpoll':
                self.exitpoll(msg, chat_id, from_id, chat_type)


#TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(pave_event_space())(
        per_chat_id(), create_open, MessageCounter, timeout=86400),
])
bot_name = '@' + bot.getMe()['username']
logging.info('Bot started')
bot.message_loop(run_forever='Listening ...')

