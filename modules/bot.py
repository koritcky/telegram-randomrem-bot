import telebot
from telebot import apihelper
import random
from threading import Thread
import re

import schedule
import modules.buttons as buttons
from db.users_db import Users
from modules.scheduler import MyThread


# Connect to proxy
password = 'Zetsalexproxy'
apihelper.proxy = {'https': f'socks5://alexproxy:{password}@80.211.167.10:1081'}

# Run bot
API = '1154226858:AAEuhWtqnsaxRazWr7-AoXZa89Cg6rNmNC8'
bot = telebot.TeleBot(API)

# Initialize db
users = Users('db/users.db')

# Queue for pausing/activation remainders flow
threads = {}
temp_msg = {}

# Create buttons
yn_keyboard = buttons.yn_keyboard()
int_keyboard = buttons.int_keyboard()

# Initial parameters for the sake of testing
init_reminders = ['Breathe!', 'Call mom']
init_period = 20



@bot.message_handler(commands=['help'])
def help(message):
    chat_id = message.from_user.id

    text = 'Hi, human! I can send you random reminders every sometimes. ' \
           'You can add reminder just by sending me it. ' \
           'To view and delete existing reminders type /remove or /list . ' \
           'Use /period to change average time intervals. ' \
           '/deactivate and /activate me whenever you are tired of reminders or set /active_time' \
           ''

    bot.send_message(chat_id, text=text)


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        users.insert(chat_id, init_reminders, init_period)
        threads[chat_id] = MyThread(chat_id, users, bot)
        status(message)


#######################################
@bot.message_handler(commands=['random'])
def show_random_once(message):
    """Show random reminder immediately"""
    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        threads[chat_id] = MyThread(chat_id, users, bot)

    bot.send_message(chat_id, random.choice(users.select(chat_id, 'reminders')))
#######################################


#######################################
@bot.message_handler(commands=['remove', 'list'])
def remove_reminder(message):
    """Remove the reminder"""
    message
    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        threads[chat_id] = MyThread(chat_id, users, bot)

    reminders = users.select(chat_id, 'reminders')
    if len(reminders) > 0:
        keyboard = buttons.create_buttons(reminders, 'rr')
        bot.send_message(chat_id,
                         'Click on the reminder if you want to remove it',
                         reply_markup=keyboard)
    else:
        bot.send_message(chat_id,
                         'I have no reminders! Type in one.')


@bot.callback_query_handler(lambda call: call.data[:2] == 'rr')
def callback_remove_reminder(call):
    chat_id = call.message.chat.id
    ind = int(call.data[2:])
    reminder = users.select(chat_id, 'reminders')[ind]
    users.remove_reminder(chat_id, reminder)
    threads[chat_id].changes_queue.put('reminders')

    if len(users.select(chat_id, 'reminders')) == 0:
        users.update(chat_id, 'status', 0)
        threads[chat_id].changes_queue.put('status')

    bot.answer_callback_query(callback_query_id=call.id,
                              show_alert=False,
                              text=f"Reminder \"{reminder}\" is removed")

    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
#######################################


@bot.message_handler(commands=['deactivate'])
def deactivate(message):
    chat_id = message.from_user.id
    if chat_id not in threads.keys():
        threads[chat_id] = MyThread(chat_id, users, bot)

    users.update(chat_id, 'status', 0)
    threads[chat_id].changes_queue.put('status')

    bot.send_message(chat_id, 'Now I am *sleeping*', parse_mode='markdown')


@bot.message_handler(commands=['activate'])
def activate(message):
    chat_id = message.from_user.id

    if chat_id not in threads.keys():
        threads[chat_id] = MyThread(chat_id, users, bot)

    users.update(chat_id, 'status', 1)
    threads[chat_id].changes_queue.put('status')

    bot.send_message(chat_id, 'Now I am *activated*', parse_mode='markdown')


@bot.message_handler(commands=['status'])
def status(message):
    chat_id = message.from_user.id

    if chat_id not in threads.keys():
        threads[chat_id] = MyThread(chat_id, users, bot)

    is_active = users.select(chat_id, 'status')
    period = int(users.select(chat_id, 'period'))
    if is_active:
        bot.send_message(chat_id,
                         f'I am *active* and sending you random reminders approximately every *{period}* seconds. '
                         'But you can /deactivate me.', parse_mode='markdown')
    else:
        bot.send_message(chat_id, 'I am *sleeping*. '
                                  f'But I can send you random reminders approximately every *{period}* seconds. '
                                  'If you /activate me, of course.', parse_mode='markdown')


#######################################
@bot.message_handler(commands=['period'])
def set_period(message):
    chat_id = message.from_user.id

    if chat_id not in threads.keys():
        threads[chat_id] = MyThread(chat_id, users, bot)

    current_period = int(users.select(chat_id, 'period'))
    bot.send_message(chat_id,
                     f'Current message period is *{current_period} seconds*. You can change it to:',
                     reply_markup=int_keyboard,
                     parse_mode='markdown')


@bot.callback_query_handler(lambda call: call.data in ['0.5', '1', '2', '3', '5', '0'])
def callback_set_period(call):
    """For set_period"""
    chat_id = call.message.chat.id
    try:
        period = float(call.data) * 3600  # Convert to seconds
        if period > 0:
            users.update(chat_id, 'period', period)
            threads[chat_id].changes_queue.put('period')
            bot.answer_callback_query(callback_query_id=call.id,
                                      show_alert=False,
                                      text=f"Period is changed to {call.data} hours")
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            msg = bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text="Type in period in seconds")
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

            bot.send_message(chat_id,
                             text=f"Period is changed to *{int(period)} seconds*",
                             parse_mode='markdown')
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
        threads[chat_id] = MyThread(chat_id, users, bot)

    if len(message.text) > 4096:
        bot.send_message(chat_id, 'Your message is too long. Use less than 4096 symbols')
        return False

    msg = message.text
    temp_msg[chat_id] = msg

    if msg in users.select(chat_id, 'reminders'):
        bot.send_message(chat_id,
                         f"*\"{msg}\"* is already in the pool",
                         parse_mode='markdown')
    else:
        bot.send_message(chat_id,
                         f'Add *\"{msg}\"* to the reminders?',
                         reply_markup=yn_keyboard,
                         parse_mode='markdown')


@bot.callback_query_handler(lambda call: call.data in ['yes', 'no'])
def callback_new_reminder(call):
    """For new_reminder"""
    chat_id = call.message.chat.id
    if call.data == "yes":
        msg = temp_msg[chat_id]
        try:
            users.add_reminder(chat_id, msg)
        except ValueError:
            bot.send_message(chat_id,
                             f"*\"{msg}\"* is already in the pool",
                             parse_mode='markdown')
        threads[chat_id].changes_queue.put('reminders')
        bot.answer_callback_query(callback_query_id=call.id,
                                  show_alert=False,
                                  text=f"\"{msg}\" is now in the pool")

    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
#######################################

@bot.message_handler(content_types=['photo', 'video', 'sticker', 'audio', 'voice'])
def sorry(message):
    chat_id = message.from_user.id
    bot.send_message(chat_id, 'Sorry, I can handle only text reminders. But stay updated!')

def main():
    Thread(target=bot.polling, kwargs={'none_stop': True, 'interval': 0}).start()


# #######################################
# @bot.message_handler(commands=['active_time'])
# def active_time(message):
#     chat_id = message.from_user.id
#     active_time = users.select(chat_id, 'active_time')
#     msg = bot.send_message(chat_id,
#                            f'Your current active time is *{active_time}*. '
#                            'Set new time interval in 24-hour format:'
#                            ' "HH:MM-HH:MM"',
#                            parse_mode='markdown')
#     bot.register_next_step_handler(msg, set_active_time)
#
#
# def set_active_time(message):
#     chat_id = message.from_user.id
#
#     if chat_id not in threads.keys():
#         threads[chat_id] = MyThread(chat_id, users, bot)
#
#     msg = message.text
#     if re.match('(^2[0-3]|[01]?[0-9]):([0-5]?[0-9])-(2[0-3]|[01]?[0-9]):([0-5]?[0-9])$', msg):
#         users.update(chat_id, 'active_time', msg)
#         start, end = msg.split('-')
#         print(start)
#         print(end)
#
#         tag = 'at' + str(chat_id)
#         schedule.clear(tag)
#         schedule.every().day.at(end).do(threads[chat_id].delete_schedule).tag(tag)
#         schedule.every().day.at(start).do(threads[chat_id].create_schedule).tag(tag)
#         bot.send_message(chat_id, f'Now I am sending you messages only when the time is in the interval *{msg}*',
#                          parse_mode='markdown')
#     else:
#         bot.send_message(chat_id, f'I dont understand =( '
#                                   'Set new time interval in 24-hour format:'
#                                   ' "HH:MM-HH:MM".')
#         bot.register_next_step_handler(message, set_active_time)
# #######################################