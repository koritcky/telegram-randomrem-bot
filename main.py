import telebot

from telebot import apihelper
import random
import schedule
from threading import Thread
import time
import queue

from buttons import create_buttons

# Connect to proxy
apihelper.proxy = {'https': 'socks5://alexproxy:Zetsalexproxy@80.211.167.10:1081'}

# Run bot
bot = telebot.TeleBot('1154226858:AAEuhWtqnsaxRazWr7-AoXZa89Cg6rNmNC8')

# Queue for pausing/activation remainders flow
is_active_queue = queue.Queue()
id_queues = []
# Create buttons
yn_keyboard, int_keyboard = create_buttons()
# chat_id: {'reminders': ['Stay hydrated', 'Breathe', 'Keep your posture'],
#           'period': 5,
#           'eps': 1}
db = {
      }
# Initial parameters
reminders = {}
init_reminders = ['Stay hydrated', 'Breathe', 'Keep your posture']

intervals = {}
init_interval = {'period': 5, 'eps': 1}


# Main function, hehe
def send(chat_id):
    bot.send_message(chat_id, random.choice(reminders[chat_id]))


@bot.message_handler(commands=['start'])
def initiate(message):
    chat_id = message.from_user.id

    reminders[chat_id] = init_reminders
    intervals[chat_id] = init_interval
    id_queues[chat_id] = queue.Queue()

    start = intervals[chat_id]['period'] - intervals[chat_id]['eps']
    end = intervals[chat_id]['period'] + intervals[chat_id]['eps']
    schedule.every(start).to(end).seconds.do(send, chat_id)


@bot.message_handler(commands=['list'])
def show_pull(message):
    chat_id = message.from_user.id
    [bot.send_message(chat_id, str(msg)) for msg in reminders[chat_id]]


@bot.message_handler(commands=['random'])
def show_random_once(message):
    chat_id = message.from_user.id
    bot.send_message(chat_id, random.choice(reminders[chat_id]))


# @bot.message_handler(commands=['show_random_regularly'])
# def show_random_regular(message):
#     chat_id = message.from_user.id


@bot.message_handler(commands=['pause'])
def send_random_regular(message):
    is_active_queue.put(False)

    # bot.send_message(id, 'Resting')


@bot.message_handler(commands=['activate'])
def send_random_regular(message):
    is_active_queue.put(True)
    # bot.send_message(id, 'Working')


@bot.message_handler(commands=['period'])
def set_interval(message):
    bot.send_message(message.from_user.id,
                     f'Choose period for reminders',
                     reply_markup=int_keyboard)


@bot.callback_query_handler(lambda call: call.data in ['0.5', '1', '2', '3', '5', '0'])
def callback_set_interval(call):
    """For set_interval"""
    global last_call_id
    last_call_id = call.id
    chat_id = call.message.chat.id
    try:
        period = float(call.data) * 3600  # Convert to seconds
        if period > 0:
            intervals[chat_id]['period'] = period
            intervals[chat_id]['eps'] = period * 0.2
            bot.answer_callback_query(callback_query_id=call.id,
                                      show_alert=False,
                                      text=f"Interval is changed to {call.data} hours")
            id_queue.put(chat_id)
        else:
            msg = bot.send_message(call.message.chat.id, 'Type in period in seconds')
            bot.register_next_step_handler(msg, set_interval_manual)

    except ValueError:
        pass


@bot.message_handler(content_types=['text'])
def set_interval_manual(message):
    chat_id = message.from_user.id
    try:
        period = int(message.text)
        if period > 0:
            intervals[chat_id]['period'] = period
            intervals[chat_id]['eps'] = period * 0.2
            bot.answer_callback_query(callback_query_id=last_call_id,
                                      show_alert=False,
                                      text=f"Interval is changed to {period / 60} minutes")
        else:
            bot.send_message(chat_id, 'Better try natural numbers')
            bot.register_next_step_handler(message, set_interval_manual)
    except ValueError:
        bot.send_message(chat_id, 'Better try natural numbers')
        bot.register_next_step_handler(message, set_interval_manual)


@bot.message_handler(content_types=['text'])
def new_reminder(message):
    global temp_msg
    temp_msg = message.text
    bot.send_message(message.from_user.id, f'Add \"{message.text}\" to the reminder spool?', reply_markup=yn_keyboard)


@bot.callback_query_handler(lambda call: call.data in ['yes', 'no'])
def callback_new_reminder(call):
    """For new_reminder"""
    chat_id = call.message.chat.id
    if call.data == "yes":
        reminders[chat_id].append(temp_msg)
        bot.answer_callback_query(callback_query_id=call.id,
                                  show_alert=False,
                                  text=f"\"{temp_msg}\" is now in the pool",
                                  cache_time=10)


def scheduling(is_active_queue, id_queue):
    is_active = True

    while True:
        try:
            is_active = is_active_queue.get(timeout=0.1)
        except queue.Empty:
            pass

        try:
            chat_id = id_queue.get(timeout=0.1)
            schedule.cancel_job(send, chat_id)
            start = intervals[chat_id]['period'] - intervals[chat_id]['eps']
            end = intervals[chat_id]['period'] + intervals[chat_id]['eps']
            schedule.every(start).to(end).seconds.do(send, chat_id)
        except queue.Empty:
            pass

        if is_active:
            schedule.run_pending()

        time.sleep(1)


Thread(target=scheduling, args=(is_active_queue, id_queue,)).start()

Thread(target=bot.polling, kwargs={'none_stop': True, 'interval': 0}).start()
