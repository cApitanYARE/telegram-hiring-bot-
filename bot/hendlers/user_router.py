import os
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, CallbackQuery

from bot.create_bot import bot
from bot.db_handler.db_funk import select_user_data, insert_user, select_all_vacancies, insert_data_review, select_search_vacancie, select_data_user_reviews, select_data_user_get_messages, insert_data_for_hr_about_review
from bot.keyboards.kbs import main_kb
from bot.keyboards.inline_kbs import sent_review_inline_kb, author_link_kb

from aiogram.utils.chat_action import ChatActionSender

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.utils.utils import process_txt, process_docx, process_pdf

from aiogram.filters.callback_data import CallbackData

import asyncio

import psycopg2
from psycopg2 import errors

import re


from bot.ai.candidate_schemas import CandidateProfile
from bot.ai.candidate_graph import candidate_bot_app
from langchain_core.messages import messages_from_dict, messages_to_dict, HumanMessage, BaseMessage
user_router = Router()

universe_text = ('To learn more, use the buttons below or select a command from the menu.')

@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        user_info = await select_user_data(user_id=message.from_user.id)
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
async def hendle_document(message: Message, bot: bot, state: FSMContext):
    document = message.document
    file_id = document.file_id
    file_name = document.file_name

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    download_dir = os.path.join(BASE_DIR, "download_resume")
    os.makedirs(download_dir, exist_ok=True)
    destination = os.path.join(download_dir, f"{file_id}_{document.file_name}")

    await bot.download_file(file_path, destination)

    current_state_str = await state.get_state()

    if file_name.endswith('.txt'):
        await process_txt(destination, message)
    elif file_name.endswith('.docx'):
        await process_docx(destination, message)
    elif file_name.endswith('.pdf'):
        await process_pdf(destination, message)

    if current_state_str == Form.screening_active.state:
        user_data = await state.get_data()
        graph_state = user_data.get("graph_state")

        if graph_state:
            graph_state["chat_history"].append({"role": "system", "content": f"USER_CV_TEXT: {raw_cv_text}"})
            
            graph_state["current_node"] = "EXTRACT_CV"
            
            from bot.ai.candidate_graph import candidate_bot_app
            updated_state = await candidate_bot_app.ainvoke(graph_state)
            
            ai_msg = updated_state["chat_history"][-1]["content"]
            await message.answer(ai_msg)
            
            await state.update_data(graph_state=updated_state)
            return 

    response_text = f'📄 File {file_name} has been processed. {universe_text}'
    await message.answer(text=response_text, reply_markup=main_kb(message.from_user.id))

@user_router.message(F.text == "📄 All vacancies")
async def select_all_vacancie(message: Message, bot: bot):
    vacancies = await select_all_vacancies()
    
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
        print(type(vacancy.get('id'))) 
        await message.answer(
            text=response_text, 
            reply_markup=sent_review_inline_kb(vacancy.get('id')),
        )

class Form(StatesGroup): 
    screening_active = State()

@user_router.callback_query(F.data.startswith("vacancy_respond:"))
async def vacancy_respond(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    vacancy_id = callback.data.split(":")[1]
    vacancy_data = await select_search_vacancie(vacancy_id)
    vacancy_data = dict(vacancy_data[0]) if vacancy_data else None

    if not vacancy_data:
        await callback.message.answer("На жаль, вакансію не знайдено.")
        return

    vacancy_data.pop("created_at", None)
    
    first_question = "Hello! Let's start the interview. What's your location (city, town, or country)?"
    initial_state = {
        "messages": [],
        "vacancy_data": vacancy_data,
        "candidate": CandidateProfile().model_dump(),
        "next_question": first_question,
        "is_completed": False,
    }

    await state.update_data(agent_state=initial_state)
    await state.set_state(Form.screening_active)
    
    await callback.message.answer(initial_state["next_question"])
   
@user_router.message(Form.screening_active, F.text)
async def handle_ai_interview_chat(message: Message, state: FSMContext):
    data = await state.get_data()
    agent_state: dict = data.get("agent_state")
 
    if not agent_state:
        await message.answer("Сесію інтерв'ю не знайдено. Будь ласка, відгукніться на вакансію знову.")
        await state.clear()
        return

    raw_messages = agent_state.get("messages", [])
    if raw_messages:
        agent_state["messages"] = messages_from_dict(raw_messages)
    else:
        agent_state["messages"] = []

    input_state = {
        **agent_state,
        "messages": agent_state["messages"] + [HumanMessage(content=message.text)]
    }
 
    updated_state: dict = await candidate_bot_app.ainvoke(input_state)
 
    cleaned_messages = []
    for msg in updated_state.get("messages", []):
        if isinstance(msg, BaseMessage):
            cleaned_messages.extend(messages_to_dict([msg]))
        elif isinstance(msg, dict):
            cleaned_messages.append(msg)

    updated_state["messages"] = cleaned_messages
 
    await state.update_data(agent_state=updated_state)

    vacancy_data = agent_state.get("vacancy_data", {})
    vacancy_id = vacancy_data.get("id")
    id_user = message.from_user.id

    result_interview = updated_state.get("candidate")
    result_interview["id_vacancy"] = int(vacancy_id)
    result_interview["id_user"] = int(id_user)
    result_interview["experience"] = str(result_interview["experience"])
    result_interview["github"] = str(result_interview["github"])
    #
    result_interview["status"] = "pending"
    if updated_state.get("is_completed"):
        await message.answer("Thank you! Your profile has been successfully completed. We will contact you shortly!")
        print(updated_state.get("candidate"))
        try:
            await insert_data_for_hr_about_review(updated_state.get("candidate"))#table_name="for_hr_about_review"
            await insert_data_review(updated_state.get("candidate"))
        except psycopg2.Error as e:
            print(f"DB error {e}")
        await state.clear()
    else:
        await message.answer(updated_state["next_question"])
 

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

    vacancies_list = []

    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        
        if input_data.isdigit():
            vacancies_list = await select_search_vacancie(id_vacancy=int(input_data))
        else:
            try: 
                response = await openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=input_data
                )
                embedding_vector = response.data[0].embedding
                
                vacancies_list = await select_search_vacancie(embedding_vector=embedding_vector)
                
            except Exception as e:
                print(f"OpenAI error during search: {e}")
                await message.answer("❌ Error processing your request via AI. Try typing simpler keywords.")
                await state.clear()
                return

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
        user_review = await select_data_user_reviews(user_id)

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

@user_router.message(F.text == "💬 Incoming messages")
async def process_search_message_to_user(message: Message, bot: bot,state):
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        user_id = message.from_user.id
        messages_to_user = await select_data_user_get_messages(user_id)
        if not messages_to_user:
            await message.answer("Nobody have send you messages yet 😔")
            await state.clear()
            return

        await message.answer(f"🔍 Found {len(messages_to_user)} messages:")
        
        for review in messages_to_user:
            skills = review.get('skills')
            skills_str = ", ".join(skills) if isinstance(skills, list) else (skills or 'Not specified')

            response_text = (
                f"📋 *Vacancy ID: {review.get('id_vacancie')}*\n\n"
                f"🏢 *Company:* {review.get('company_name') or 'Not specified'}\n"
                f"💼 *Job Position:* {review.get('job_position') or 'Not specified'}\n"
                f"🛠  *Main skills:*\n{skills_str}\n\n"
                f"💬  *Answear*\n{review.get('text') or 'Not specified'}\n"
            )
            await message.answer(
                text=response_text
            )
        await state.clear()
