import telebot

from telebot import apihelper
import random
from threading import Thread

import buttons
from users_db import Users
from scheduler import MyThread



# Connect to proxy
password = 'Zetsalexproxy'
apihelper.proxy = {'https': f'socks5://alexproxy:{password}@80.211.167.10:1081'}

# Run bot
API = '1154226858:AAEuhWtqnsaxRazWr7-AoXZa89Cg6rNmNC8'
bot = telebot.TeleBot(API)

# Initialize db
users = Users('users.db')

# Queue for pausing/activation remainders flow
threads = {}

# Create buttons
yn_keyboard = buttons.yn_keyboard()
int_keyboard = buttons.int_keyboard()

# Initial parameters for the sake of testing
init_reminders = ['Breathe!', 'Call mom']
init_period = 10



@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.from_user.id

    if chat_id not in threads.keys():
        users.insert(chat_id, init_reminders, init_period)
        threads[chat_id] = MyThread(chat_id, users, bot)


#######################################
@bot.message_handler(commands=['random'])
def show_random_once(message):
    """Show random reminder immediately"""
    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        start(message)

    bot.send_message(chat_id, random.choice(users.select(chat_id, 'reminders')))
#######################################




#######################################
@bot.message_handler(commands=['remove', 'list'])
def remove_reminder(message):
    """Remove the reminder"""

    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        start(message)

    reminders = users.select(chat_id, 'reminders')
    keyboard = buttons.create_buttons(reminders)
    bot.send_message(message.from_user.id, 'Click on the reminder if you want to remove it', reply_markup=keyboard)


@bot.callback_query_handler(lambda call: call.data in users.select(call.message.chat.id, 'reminders'))
def callback_remove_reminder(call):
    chat_id = call.message.chat.id
    users.remove_reminder(chat_id, call.data)
    threads[chat_id].changes_queue.put('reminders')
    bot.answer_callback_query(callback_query_id=call.id,
                              show_alert=False,
                              text=f"\"{call.data}\" is removed")
#######################################


#######################################
@bot.message_handler(commands=['deactivate'])
def deactivate(message):
    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        start(message)

    users.update(chat_id, 'status', 0)
    threads[chat_id].changes_queue.put('status')

    bot.send_message(chat_id, 'Now I am *sleeping*', parse_mode='markdown')


@bot.message_handler(commands=['activate'])
def activate(message):
    chat_id = message.from_user.id
    users.update(chat_id, 'status', 1)
    threads[chat_id].changes_queue.put('status')

    bot.send_message(chat_id, 'Now I am *activated*', parse_mode='markdown')
#######################################

@bot.message_handler(commands=['status'])
def status(message):
    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        start(message)
    is_active = users.select(chat_id, 'status')
    period = users.select(chat_id, 'period')
    if is_active:
        bot.send_message(chat_id, f'I am *active* and sending you random reminders approximately every *{period}* second. '
                                  'But you can /deactivate me', parse_mode='markdown')
    else:
        bot.send_message(chat_id, 'I am *sleeping*. '
                                  f'But I can send you random reminders approximately every *{period}* second. '
                                  'If you /activate me, of course.', parse_mode='markdown')




#######################################
@bot.message_handler(commands=['period'])
def set_period(message):
    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        start(message)
    current_period = int(users.select(chat_id, 'period'))
    bot.send_message(chat_id,
                     f'Current message period is *{current_period} seconds*. You can change it to:',
                     reply_markup=int_keyboard,
                     parse_mode='markdown')


@bot.callback_query_handler(lambda call: call.data in ['0.5', '1', '2', '3', '5', '0'])
def callback_set_period(call):
    """For set_interval"""
    global last_call_id
    last_call_id = call.id
    chat_id = call.message.chat.id
    try:
        period = float(call.data) * 3600  # Convert to seconds
        if period > 0:
            users.update(chat_id, 'period', period)
            threads[chat_id].changes_queue.put('period')
            bot.answer_callback_query(callback_query_id=call.id,
                                      show_alert=False,
                                      text=f"Period is changed to {call.data} hours")
            # id_queue.put(chat_id)
        else:
            msg = bot.send_message(call.message.chat.id, 'Type in period in seconds')
            bot.register_next_step_handler(msg, set_period_manual)

    except ValueError:
        pass


def set_period_manual(message):
    chat_id = message.from_user.id
    try:
        period = float(message.text)
        if period > 0:
            users.update(chat_id, 'period', period)
            threads[chat_id].changes_queue.put('period')
            bot.answer_callback_query(callback_query_id=last_call_id,
                                      show_alert=False,
                                      text=f"Period is changed to {int(period)} seconds")
        else:
            bot.send_message(chat_id, 'Better try natural numbers')
            bot.register_next_step_handler(message, set_period_manual)
    except ValueError:
        bot.send_message(chat_id, 'Better try natural numbers')
        bot.register_next_step_handler(message, set_period_manual)
#######################################

@bot.message_handler(commands=['clear'])
def clear_reminders(message):
    chat_id = message.from_user.id
    users.update(chat_id, 'reminders', init_reminders)

#######################################
@bot.message_handler(content_types=['text'])
def new_reminder(message):
    """Create new reminder from getting message"""
    chat_id = message.from_user.id

    if chat_id not in threads.keys():
        start(message)

    if len(message.text) > 4096:
        bot.send_message(chat_id, 'Your message is too long. Use less than 4096 symbols')


    global temp_msg
    temp_msg = message.text
    if temp_msg in users.select(chat_id, 'reminders'):
        bot.send_message(chat_id, f"\"{temp_msg}\" is already in the pool")
    else:
        bot.send_message(chat_id, f'Add \"{message.text}\" to the reminders?', reply_markup=yn_keyboard)


@bot.callback_query_handler(lambda call: call.data in ['yes', 'no'])
def callback_new_reminder(call):
    """For new_reminder"""
    chat_id = call.message.chat.id
    if call.data == "yes":
        users.add_reminder(chat_id, temp_msg)
        threads[chat_id].changes_queue.put('reminders')
        bot.answer_callback_query(callback_query_id=call.id,
                                  show_alert=False,
                                  text=f"\"{temp_msg}\" is now in the pool")
#######################################



Thread(target=bot.polling, kwargs={'none_stop': True, 'interval': 0}).start()
