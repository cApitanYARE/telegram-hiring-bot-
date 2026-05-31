from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

def author_link_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Author's GitHub", url ='https://github.com/cApitanYARE')],
        [InlineKeyboardButton(text="Author's Linkedin", url="https://www.linkedin.com/in/denis-ivanyuta-2bbaab2bb/")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

def sent_review_inline_kb(vacancy_id):
    inline_kb_list = [
        [InlineKeyboardButton(text="Respond", callback_data=f"vacancy_respond:{vacancy_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def sent_answear_on_review_inline_kb(user_id,vacancy_id, hr_id):
    inline_kb_list = [
        [
        InlineKeyboardButton(text="Respond", callback_data=f"vacancy_respond_hr_to_user:{user_id}:{vacancy_id}:{hr_id}"),
        InlineKeyboardButton(text="Reject", callback_data=f"vacancy_reject:{user_id}:{vacancy_id}:{hr_id}"),
        InlineKeyboardButton(text="Add to Talent Pool", callback_data=f"vacancy_talent_pool:{user_id}:{vacancy_id}:{hr_id}")
    
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)