import os
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message

from bot.create_bot import bot
from bot.db_handler.db_funk import get_user_data, insert_user, get_all_vacancies
from bot.keyboards.kbs import main_kb

from aiogram.utils.chat_action import ChatActionSender

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.utils.utils import process_txt, process_docx, process_pdf

user_router = Router()

universe_text = ('To learn more, use the buttons below or select a command from the menu.')

@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        user_info = await get_user_data(user_id=message.from_user.id)

    if user_info:
        response_text = f'{user_info.get("full_name")}, see you in my data base. {universe_text}'
    else: 
        await insert_user(user_data={
            'user_id': message.from_user.id,
            'full_name': message.from_user.full_name,
            'user_login': message.from_user.username,
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
            reply_markup=main_kb(message.from_user.id), 
        )