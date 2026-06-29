import os
import asyncio

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters.callback_data import CallbackData

from aiogram.fsm.context import FSMContext

from aiogram.utils.chat_action import ChatActionSender
from bot.create_bot import admins, bot
from bot.db_handler.db_funk import select_all_users, insert_vacancies, select_all_vacancies, select_data_all_reviews, select_user_data, update_user_status,insert_data_user_get_messages, select_data_for_hr_about_review, select_search_vacancie
#insert_user_to_talant_pool
from bot.keyboards.kbs import home_page_kb, main_kb
from bot.keyboards.inline_kbs import sent_answear_on_review_inline_kb

from bot.utils.utils import process_txt, process_docx, process_pdf

from tkinter import Tk 
from tkinter.filedialog import askopenfilename

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.ai.candidate_agent import analyze_interviewer

from datetime import datetime

import re

admin_router = Router()

def get_file_path():
    root = Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)

    file_path = askopenfilename(
        title="Select file",
        filetypes=[
            ("PDF files", "*.pdf"),
            ("Word files", "*.docx *.doc"),
            ("Text files", "*.txt"),
        ]
    )
    
    root.destroy() 
    return file_path

class VacancyStates(StatesGroup):
    wait_for_file = State()

@admin_router.message(F.text == "⚙️ Add a vacancy")
async def select_file(message: Message, state: FSMContext):
    await message.answer("Select file on tour PC...")

    #file_path = await asyncio.to_thread(get_file_path)
    await state.set_state(VacancyStates.wait_for_file)

    #if file_path:
    #    await message.answer(f"You select file: {file_path}")
    #else:
    #    await message.answer("You cancel selection")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@admin_router.message(VacancyStates.wait_for_file, F.document)
async def uploud_vacancies(message: Message, bot: bot, state: FSMContext):
    document = message.document
    file_id = document.file_id
    file_name = document.file_name

    if not (file_name.endswith('.txt') or file_name.endswith('.docx') or file_name.endswith('.pdf')):
        await message.answer("❌ Error. You must send .txt, .docx або .pdf")
        return

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

        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        vacancy_text = (
            f"Position and Skills {data["job_position"]}, {data["skills"]}, {data["nice_to_have"]}."
            f" Required Experience: {data["experience"]}."
        )

        try: 
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=vacancy_text
            )
            embedding_vector = response.data[0].embedding
        except Exception as e:
            print(f"OpenAI error: {e}")
            return None

        data["embedding"] = embedding_vector

        new_id = await insert_vacancies(data)
        await state.clear()

        if not new_id:
            length = await select_search_vacancie(count=True) 
            new_id = length + 1

        response_text = f"Vacancy seccsesfully added at DB with ID {new_id}"

    await message.answer(text=response_text, reply_markup=main_kb(message.from_user.id))

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

@admin_router.message(F.text == "⚙️ Received Applications")
async def get_received_applications(message: Message):
    all_reviews = await select_data_all_reviews()

    hr_id = message.from_user.id

    if not all_reviews:
        await message.answer("📭 There are no 'Received Applications' in the database yet.")
        return

    for review in all_reviews:
        skills = review.get('skills')
        skills_str = ", ".join(skills) if isinstance(skills, list) else (skills or 'Not specified')
        
        candidate_name = review.get('full_name') or 'Not specified'
        user_login = review.get('user_login')
        username_str = f" (@{user_login})" if user_login else ""

        candidate_data = await select_data_for_hr_about_review(int(review.get('id_vacancie')), int(review.get('id_user')))
        vacancy_data = await select_search_vacancie(int(review.get('id_vacancie')))

        rate_candidate = await analyze_interviewer(vacancy_data, candidate_data)

        if review.get('status'):
            status_str = "🟢 In work"
        else:
            status_str = "🔴 Closed"

        #print(type(rate_candidate))

        response_text = (
            # --- About Vacancy ---
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Information about Vacancy</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 <b>Status:</b> {status_str}\n"
            f"📋 <b>Vacancy ID:</b> {review.get('id_vacancie')}\n"
            f"🏢 <b>Company:</b> {review.get('company_name')}\n"
            f"💼 <b>Job Position:</b> {review.get('job_position') or 'Not specified'}\n\n"

            # --- About Candidate ---
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Information about Candidate</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Candidate:</b> {candidate_name}{username_str}\n"
            f"⏳ <b>Experience:</b> {review.get('experience') or 'Not specified'} year\n"
            f"📍 <b>Location:</b> {review.get('location') or 'Not specified'}\n"
            f"🔄 <b>Work Mode:</b> {review.get('work_mode') or 'Not specified'}\n"
            f"🔗 <b>GitHub Link:</b> {review.get('git_hub_url') or 'Not specified'}\n\n"
            f"🛠 <b>Main skills (Skills):</b>\n{skills_str}\n\n"

            # --- AI ---
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 <b>Response from AI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Percentage:</b> {rate_candidate.match_percentage}%\n"
            f"⚖️ <b>Verdict:</b> {rate_candidate.verdict}\n\n"
            f"✅ <b>Matched Skills:</b> {rate_candidate.matched_skills}\n"
            f"❌ <b>Missing Skills:</b> {rate_candidate.missing_skills}\n\n"
            f"👍 <b>Pros:</b> {rate_candidate.pros}\n\n"
            f"👎 <b>Cons:</b> {rate_candidate.cons}\n\n"
            f"📋 <b>Summary:</b> {rate_candidate.summary}\n"
            f"📋 <b>github_summary:</b>{rate_candidate.github_summary}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        await message.answer(
            text=response_text,
            reply_markup=sent_answear_on_review_inline_kb(review.get('id_user'), review.get('id_vacancie'), hr_id),
        )

@admin_router.callback_query(F.data.startswith("vacancy_reject:"))
async def vacancy_reject(callback: CallbackQuery, state: FSMContext):
    await callback.answer()


    data_parts = callback.data.split(":")
    user_id = int(data_parts[1])     
    vacancy_id = int(data_parts[2])

    user_data = await select_user_data(user_id)
    vacancy_data = await select_search_vacancie(vacancy_id)
    print(vacancy_data)
    if user_data and isinstance(user_data, dict):
        candidate_name = user_data.get('full_name') or 'Not specified'
        user_login = user_data.get('user_login')
        username_str = f" (@{user_login})" if user_login else ""

        await update_user_status(int(user_id),int(vacancy_id), "reject")
    else:
        candidate_name = f"ID: {user_id}"
        username_str = ""

    job_position = vacancy_data[0].get('job_position')
    await callback.message.edit_text(
        text=f"❌ The candidate <b>{candidate_name}</b>{username_str} is rejected on vacancy ID: {vacancy_id}.\nPosition: {job_position}"
    )
    await asyncio.sleep(5)
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"{e}")

@admin_router.callback_query(F.data.startswith("vacancy_talent_pool:"))
async def candidate_move_to_talant_pool(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data_parts = callback.data.split(":")

    user_id = int(data_parts[1])     
    hr_id = int(data_parts[2])
    experience = str(data_parts[3])
    location = str(data_parts[4])
    skills_str = str(data_parts[5])
    vacancy_id = int(data_parts[6])

    user_data = await select_user_data(user_id)

    if user_data and isinstance(user_data, dict):
        candidate_name = user_data.get('full_name') or 'Not specified'
        user_login = user_data.get('user_login')
        username_str = f" (@{user_login})" if user_login else ""

        #await insert_user_to_talant_pool(str(user_id),str(location),str(skills_str),str(experience))
        await update_user_status(str(user_id),str(vacancy_id), "pool")
    else:
        candidate_name = f"ID: {user_id}"
        username_str = ""

    await callback.message.edit_text(
        text=f"📂The candidate *{candidate_name}*{username_str} is added to talent pool."
    )
    await asyncio.sleep(5)
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"{e}")

class HRResponsrState(StatesGroup):
    waiting_for_comment = State()

@admin_router.callback_query(F.data.startswith("vacancy_respond_hr_to_user:"))
async def vacancy_accept(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data_parts = callback.data.split(":")
    user_id = int(data_parts[1])     
    vacancy_id = int(data_parts[2])
    hr_id = int(data_parts[3])

    await state.update_data(
        user_id=user_id,
        vacancy_id=vacancy_id,
        hr_id=hr_id
    )

    await state.set_state(HRResponsrState.waiting_for_comment)

    await callback.message.answer("Enter your comment to the candidat:")

@admin_router.message(HRResponsrState.waiting_for_comment)
async def insert_hr_comment_to_candidate(message: Message, state: FSMContext):
    comment_text = message.text

    user_data = await state.get_data()
    user_id = user_data.get("user_id")
    vacancy_id = user_data.get("vacancy_id")
    hr_id = user_data.get("hr_id")

    await insert_data_user_get_messages(
        data={
            "hr_id": hr_id,
            "user_id": user_id,
            "vacancy_id": vacancy_id,
            "comment": comment_text  
        }
    )
    await state.clear()

    await message.answer("Your comment has been successfully saved and sent!")

