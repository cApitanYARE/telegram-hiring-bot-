import os

from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from bot.create_bot import admins, bot
from bot.db_handler.db_funk import get_all_users, add_vacancies, get_all_vacancies
from bot.keyboards.kbs import home_page_kb, main_kb
from bot.utils.utils import process_txt, process_docx, process_pdf

admin_router = Router()

@admin_router.message((F.text.endswith('⚙️ Admin panel')) & (F.from_user.id.in_(admins)))
async def get_profile(message: Message):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        all_users_data = await get_all_users()

        admin_text = (
            f'In data base <b>{len(all_users_data)}</b> people. Here is a brief information about each one:\n\n'
        )

        for user in all_users_data:
            admin_text += (
                f'Telegram ID: {user.get("user_id")}\n'
                f'Full name: {user.get("full_name")}\n'
            )

            if user.get("user_login") is not None:
                admin_text += f'Login: {user.get("user_login")}\n'

            admin_text += (
                 f'📅 Feedback sent: {user.get("date_reg")}\n'
                 f'\n〰️〰️〰️〰️〰️〰️〰️〰️〰️\n\n'
            )
        
    await message.answer(admin_text, reply_markup=home_page_kb(message.from_user.id))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@admin_router.message(F.document)
async def uploud_vacancies(message: Message, bot: bot):
    document = message.document
    file_id = document.file_id
    file_name = document.file_name

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    download_dir = os.path.join(BASE_DIR, "downloads_vacancies")
    os.makedirs(download_dir, exist_ok=True)
    destination = os.path.join(download_dir, f"{file_id}_{document.file_name}")

    await bot.download_file(file_path, destination)

    if file_name.endswith('.txt'):
        text_content = await process_txt(destination, message)
    elif file_name.endswith('.docx'):
        text_content = await process_docx(destination, message)
    elif file_name.endswith('.pdf'):
        text_content= await process_pdf(destination, message)

    data = {
            "company_name": "",
            "job_position": "",
            "location": "",
            "work_mode": "",
            "salary": "",
            "currency": "",
            "experience": "",
            "skills": [],
            "nice_to_have": [],
            "more_about_it": ""
        }

    more_about_lines = []
    capture_more_about = False

    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        lines = text_content.split('\n')
        for line in lines:
            text = line.strip()
            if not text:
                continue
                
            if "3. About company" in text:
                capture_more_about = False
                continue

            # parsing simple fields via token ":"
            if ":" in text and not capture_more_about:
                header, value = text.split(":", 1)
                header = header.lower() 
                value = value.strip()
                
                if "company_name" in header:
                    data["company_name"] = value
                elif "job_position" in header:
                    data["job_position"] = value
                elif "location" in header:
                    data["location"] = value
                elif "work_mode" in header:
                    data["work_mode"] = value
                elif "salary" in header:
                    data["salary"] = value
                elif "currency" in header:
                    data["currency"] = value
                elif "experience" in header:
                    data["experience"] = value
                elif "skills" in header:
                    data["skills"] = [s.strip() for s in value.split(",") if s.strip()]
                elif "nice_to_have" in header:
                    data["nice_to_have"] = [s.strip() for s in value.split(",") if s.strip()]
                elif "more_about_it" in header:
                    capture_more_about = True
                    if value:
                        more_about_lines.append(value)
            
            elif capture_more_about:
                more_about_lines.append(text)

        data["more_about_it"] = " ".join(more_about_lines).strip()

        skills_str = ", ".join(data["skills"]) if data["skills"] else "Not specified"
        nice_to_have_str = ", ".join(data["nice_to_have"]) if data["nice_to_have"] else "Not specified"

        await add_vacancies(data)
        response_text = "Vacancies is added at DB"
    await message.answer(text=response_text, reply_markup=main_kb(message.from_user.id))

