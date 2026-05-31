from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from bot.create_bot import admins

def main_kb(user_telegram_id: int):
    if user_telegram_id in admins:
        kb_list = [
            [KeyboardButton(text="⚙️ Add a vacancy"), KeyboardButton(text="⚙️ Received Applications")],
            [KeyboardButton(text="⚙️ Admin panel")]
        ]
    else:
        kb_list = [
            [KeyboardButton(text="🔍 Job search") ,KeyboardButton(text="Incoming messages")],
            [KeyboardButton(text="📄 All vacancies"), KeyboardButton(text="💬 My reviews")],
            [KeyboardButton(text="👤 About the author"), KeyboardButton(text="🏢 About the company")]
        ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True, 
        one_time_keyboard=False,
        input_field_placeholder="Use the menu..."
    )
    return keyboard

def home_page_kb(user_telegram_id: int):
    kb_list = [[KeyboardButton(text="Back")]]

    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️ Admin panel")])
    return ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Use the menu..."
    )
