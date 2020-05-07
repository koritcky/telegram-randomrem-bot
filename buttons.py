from telebot import types

def create_buttons(list):
    """Button creator"""
    keyboard = types.InlineKeyboardMarkup()
    for item in list:
        key = types.InlineKeyboardButton(text=str(item), callback_data=str(item))
        keyboard.add(key)

    return keyboard

def yn_keyboard():
    """Create yes/no keyboard"""
    yn_keyboard = types.InlineKeyboardMarkup()

    key_yes = types.InlineKeyboardButton(text='Yes', callback_data='yes')  # кнопка «Да»
    key_no = types.InlineKeyboardButton(text='No', callback_data='no')
    yn_keyboard.add(key_yes, key_no)  # добавляем кнопку в клавиатуру

    return yn_keyboard

def int_keyboard():
    """Create time intervals keyboard"""
    int_keyboard = types.InlineKeyboardMarkup()

    key_half = types.InlineKeyboardButton(text='30 minutes', callback_data='0.5')
    key_1 = types.InlineKeyboardButton(text='1 hour', callback_data='1')
    key_2 = types.InlineKeyboardButton(text='2 hours', callback_data='2')
    key_3 = types.InlineKeyboardButton(text='3 hours', callback_data='3')
    key_5 = types.InlineKeyboardButton(text='5 hours', callback_data='5')
    key_manual = types.InlineKeyboardButton(text='Choose manually', callback_data='0')

    int_keyboard.add(key_half, key_1, key_2, key_3, key_5, key_manual)

    return int_keyboard

