import os
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery

from bot.create_bot import bot
from bot.db_handler.db_funk import get_user_data, insert_user, get_all_vacancies, insert_data_review, search_vacancie, get_data_user_reviews
from bot.keyboards.kbs import main_kb
from bot.keyboards.inline_kbs import sent_review_inline_kb, author_link_kb

from aiogram.utils.chat_action import ChatActionSender

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.utils.utils import process_txt, process_docx, process_pdf

from aiogram.filters.callback_data import CallbackData

import asyncio

user_router = Router()

universe_text = ('To learn more, use the buttons below or select a command from the menu.')

@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        user_info = await get_user_data(user_id=message.from_user.id)
        response_text = ""
        
        if user_info:
            response_text = f'{user_info.get("full_name")}, see you in my data base. {universe_text}'
        else: 
            await insert_user(user_data={
                'user_id': message.from_user.id,
                'full_name': message.from_user.full_name,
                'user_login': message.from_user.username,
                # 'date_reg' підставиться автоматично всередині функції insert_user
            })
            response_text = f'👋 Hello, {message.from_user.full_name}! Welcome to the absolut3 hiring bot. {universe_text}'

        await message.answer(text=response_text, reply_markup=main_kb(message.from_user.id))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@user_router.message(F.document)
async def hendle_document(message: Message, bot: bot):
    document = message.document
    file_id = document.file_id
    file_name = document.file_name

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    download_dir = os.path.join(BASE_DIR, "download_resume")
    os.makedirs(download_dir, exist_ok=True)
    destination = os.path.join(download_dir, f"{file_id}_{document.file_name}")

    await bot.download_file(file_path, destination)

    if file_name.endswith('.txt'):
        await process_txt(destination, message)
    elif file_name.endswith('.docx'):
        await process_docx(destination, message)
    elif file_name.endswith('.pdf'):
        await process_pdf(destination, message)

    response_text = f' File, {file_id}being processed. {universe_text}'

    await message.answer(text=response_text, reply_markup=main_kb(message.from_user.id))

@user_router.message(F.text == "📄 All vacancies")
async def get_all_vacanciesfrom_db(message: Message, bot: bot):
    vacancies = await get_all_vacancies()
    
    if not vacancies:
        await message.answer("📭 There are no vacancies in the database yet.")
        return

    for vacancy in vacancies:
        skills = vacancy.get('skills')
        skills_str = ", ".join(skills) if isinstance(skills, list) else (skills or 'Not specified')
        
        nice_to_have = vacancy.get('nice_to_have')
        nice_to_have_str = ", ".join(nice_to_have) if isinstance(nice_to_have, list) else (nice_to_have or 'Not specified')

        response_text = (
            f"📋 *Vacancy ID: {vacancy.get('id')}*\n\n"
            f"🏢 *Company:* {vacancy.get('company_name') or 'Not specified'}\n"
            f"💼 *Job Position:* {vacancy.get('job_position') or 'Not specified'}\n"
            f"📍 *Location:* {vacancy.get('location') or 'Not specified'}\n"
            f"🔄 *Work Mode:* {vacancy.get('work_mode') or 'Not specified'}\n"
            f"💰 *Salary:* {vacancy.get('salary') or 'Not specified'} {vacancy.get('currency') or ''}\n"
            f"⏳ *Experience:* {vacancy.get('experience') or 'Not specified'}\n\n"
            f"🛠 *Main skills (Skills):*\n{skills_str}\n\n"
            f"⭐️ *Nice to have:*\n{nice_to_have_str}\n\n"
            f"📝 *About the project / Additional info:* \n{vacancy.get('more_about_it') or 'Not specified'}"
        )
        
        await message.answer(
            text=response_text, 
            reply_markup=sent_review_inline_kb(vacancy.get(id)),
        )

class Form(StatesGroup): 
    location = State()
    work_mode = State()
    experience = State()
    skills = State()

STEPS = {
    Form.location: {
        "db_key": "location", 
        "next_text": "💼 What mode of operation are you interested in?(Remote, Office, Hybrid):",
        "next_state": Form.work_mode
    },
    Form.work_mode: {
        "db_key": "work_mode", 
        "next_text": "⏳ Describe your work experience (for example: 2 years, Middle):",
        "next_state": Form.experience
    },
    Form.experience: {
        "db_key": "experience", 
        "next_text": "🛠️ List your key skills separated by commas:",
        "next_state": Form.skills
    }
}

@user_router.callback_query(F.data.startswith("vacancy_respond:"))
async def vacancy_respond(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    vacancy_id = callback.data.split(":")[1]

    await state.update_data(
        id_vacancie=str(vacancy_id),
        id_user=str(callback.from_user.id)
    )

    async with ChatActionSender.typing(bot=callback.bot, chat_id=callback.message.chat.id):
        await asyncio.sleep(1)
        await asyncio.sleep(1)
        await callback.message.answer('Hello, please write your location (city, cointry): ')
    await state.set_state(Form.location)

@user_router.message(Form.location)
@user_router.message(Form.work_mode)
@user_router.message(Form.experience)
async def process_profile_steps(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    for state_obj, config in STEPS.items():
        if state_obj.state == current_state:
            # Зберігаємо відповідь
            await state.update_data({config["db_key"]: message.text})
            # Перемикаємо на наступний стан
            await state.set_state(config["next_state"])
            
            # Задаємо наступне питання
            async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
                await asyncio.sleep(1)
                await message.answer(config["next_text"])
            return
            
@user_router.message(Form.skills)
async def process_skills_and_finish(message: Message, state: FSMContext):
    await state.update_data(skills=message.text)
    
    user_data = await state.get_data()
    
    await state.clear()
    
    try:
        await insert_data_review(user_data)
        await message.answer("🎉 Thank you! Your application has been successfully sent.")
    except Exception as e:
        await message.answer("❌ Something went wrong while saving your data.")

class SearchVacancyStates(StatesGroup):
    wait_for_query = State()

@user_router.message(F.text == "🔍 Job search")
async def process_search_query(message: Message, bot: bot,state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await message.answer("Write the name or the ID of vacancie...")
        await state.set_state(SearchVacancyStates.wait_for_query)

@user_router.message(SearchVacancyStates.wait_for_query, F.text)
async def get_vacancy_by_id_or_name(message: Message, state: FSMContext):

    input_data = message.text
    await state.update_data(search_query=input_data)

    vacancies_list = await search_vacancie(str(input_data))

    if not vacancies_list:
            await message.answer("Vacancy not found 😔")
            await state.clear()
            return
    
    await message.answer(f"🔍 Found {len(vacancies_list)} vacancies:")

    for vacancy in vacancies_list:
        skills_str = vacancy.get('skills') or 'Not specified'
        nice_to_have_str = vacancy.get('nice_to_have') or 'Not specified'

        response_text = (
                f"📋 *Vacancy ID: {vacancy.get('id')}*\n\n"
                f"🏢 *Company:* {vacancy.get('company_name') or 'Not specified'}\n"
                f"💼 *Job Position:* {vacancy.get('job_position') or 'Not specified'}\n"
                f"📍 *Location:* {vacancy.get('location') or 'Not specified'}\n"
                f"🔄 *Work Mode:* {vacancy.get('work_mode') or 'Not specified'}\n"
                f"💰 *Salary:* {vacancy.get('salary') or 'Not specified'} {vacancy.get('currency') or ''}\n"
                f"⏳ *Experience:* {vacancy.get('experience') or 'Not specified'}\n\n"
                f"🛠 *Main skills (Skills):*\n{skills_str}\n\n"
                f"⭐️ *Nice to have:*\n{nice_to_have_str}\n\n"
                f"📝 *About the project / Additional info:* \n{vacancy.get('more_about_it') or 'Not specified'}"
        )
        await message.answer(
        text=response_text, 
        reply_markup=sent_review_inline_kb(vacancy.get('id')),
        )
    await state.clear()

@user_router.message(F.text == "👤 About the author")
async def process_search_query(message: Message, bot: bot,state):
    response_text = "All info about athor can find in link bellow:"
    await message.answer(
        text=response_text,
        reply_markup=author_link_kb())

@user_router.message(F.text == "💬 My reviews")
async def process_search_user_reviews(message: Message, bot: bot,state):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        user_id = message.from_user.id
        user_review = await get_data_user_reviews(user_id)

        if not user_review:
            await message.answer("You not have reviews yet 😔")
            await state.clear()
            return

        await message.answer(f"🔍 Found {len(user_review)} reviews:")
        
        for review in user_review:
            skills = review.get('skills')
            skills_str = ", ".join(skills) if isinstance(skills, list) else (skills or 'Not specified')

            response_text = (
                    f"📋 *Vacancy ID: {review.get('id_vacancie')}*\n\n"
                    f"📋 *Status: {review.get('status')}*\n\n"
                    f"🏢 *Company:* {review.get('company_name') or 'Not specified'}\n"
                    f"💼 *Job Position:* {review.get('job_position') or 'Not specified'}\n"
                    f"💰 *Salary:* {review.get('salary') or 'Not specified'} {review.get('currency') or ''}\n"
                    f"🛠  *Main skills:*\n{skills_str}\n"
            )
            await message.answer(
            text=response_text,
            )
        await state.clear()

@user_router.message(F.text == "Incoming messages")
async def process_search_message_to_user(message: Message, bot: bot,state):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        user_id = message.from_user.id
        messages_to_user = await get_data_user_get_messages(user_id)

        if not user_review:
            await message.answer("Nobody have send you messages yet 😔")
            await state.clear()
            return

        await message.answer(f"🔍 Found {len(messages_to_user)} messages:")
        
        for review in messages_to_user:
            skills = review.get('skills')
            skills_str = ", ".join(skills) if isinstance(skills, list) else (skills or 'Not specified')

            response_text = (
                    f"📋 *Vacancy ID: {review.get('id_vacancie')}*\n\n"
                    f"📋 *Status: {review.get('status')}*\n\n"
                    f"🏢 *Company:* {review.get('company_name') or 'Not specified'}\n"
                    f"💼 *Job Position:* {review.get('job_position') or 'Not specified'}\n"
                    f"💰 *Salary:* {review.get('salary') or 'Not specified'} {review.get('currency') or ''}\n"
                    f"🛠  *Main skills:*\n{skills_str}\n"
            )
            await message.answer(
            text=response_text,
            )
        await state.clear()