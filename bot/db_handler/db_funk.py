import asyncio
import asyncpg
from decouple import config
from sqlalchemy import BigInteger, Integer, String, DateTime, Boolean, Text, DateTime, text, Identity, select
from sqlalchemy.sql import func
from bot.create_bot import db_manager
from sqlalchemy.ext.asyncio import AsyncSession
import logging
DATABASE_URL = config('DATABASE_URL')

# async def connect_to_db():
#     clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
#     conn = await asyncpg.connect(clean_url)
#     return conn

logger = logging.getLogger(__name__)

def _parse_list_to_str(data_list):
    """Converts a list (e.g., ['Python', 'SQL']) into a comma-separated string."""
    if not data_list:
        return ""
    if isinstance(data_list, list):
        return ", ".join(map(str, data_list))
    return str(data_list)

#create table
async def create_table_users(table_name='users_reg'):
    async with db_manager as client:
        await client.create_table(
            table_name=table_name,
            columns=[
                {'name': 'user_id', 'type': BigInteger, 'primary_key': True},
                {'name': 'full_name', 'type': String(255)},
                {'name': 'user_login', 'type': String(255)},
                {'name': 'date_reg', 'type': DateTime, 'default': func.now()}
            ]
        )

try:
    asyncio.get_event_loop().create_task(create_table_users())
except RuntimeError:
    pass

async def create_table_vacancies(table_name='vacancie'):
    async with db_manager as client:
        await client.create_table(
            table_name=table_name,
            columns=[
                {'name': 'id', 'type': Integer, 'primary_key': True, 'autoincrement': True},
                {'name': 'is_active', 'type': Boolean, 'server_default': text('true')},
                {'name': 'created_at', 'type': DateTime, 'server_default': text('NOW()')},
                {'name': 'company_name', 'type': String(255)},
                {'name': 'job_position', 'type': String(255)},
                {'name': 'location', 'type': String(255)},
                {'name': 'work_mode', 'type': String(255)},
                {'name': 'salary', 'type': String(255)},
                {'name': 'currency', 'type': String(10)},
                {'name': 'experience', 'type': String(255)},
                {'name': 'skills', 'type': String(255)},
                {'name': 'nice_to_have', 'type': String(255)},
                {'name': 'more_about_it', 'type': Text}
            ]
        )

async def create_table_reviews(table_name="reviews"):
    async with db_manager as client:
        await client.create_table(
            table_name=table_name,
            columns=[
                {'name': 'id', 'type': Integer, 'primary_key': True, 'autoincrement': True},
                {'name': 'id_vacancie', 'type':  String(255)},
                {'name': 'id_user', 'type': String(255)},
                {'name': 'status', 'type': Boolean, 'default': True},
                {'name': 'location', 'type': String(255)},
                {'name': 'work_mode', 'type': String(255)},
                {'name': 'experience', 'type': String(255)},
                {'name': 'skills', 'type': String(255)},
                {'name': 'data_sent', 'type': DateTime, 'default': func.now()}
            ]
        )

async def create_table_for_hr_about_review(table_name="for_hr_about_review"):
    async with db_manager as client:
        await client.create_table(
            table_name=table_name,
            columns=[
                {'name': 'id_vacancie', 'type': Integer},
                {'name': 'id_user', 'type': BigInteger},
                {'name': 'location', 'type': String(255)},
                {'name': 'work_mode', 'type': String(255)},
                {'name': 'skills', 'type': String(255)},
                {'name': 'experience', 'type': String(255)},
                {'name': 'git_hub_url', 'type': String(255)},
                {'name': 'status', 'type': String(50), 'default': 'pending'},
            ]
        )

async def create_table_messeges_to_user(table_name="messages_to_user"):
    async with db_manager as client:
        await client.create_table(
            table_name=table_name,
            columns=[
                {'name': 'id_hr', 'type': BigInteger},
                {'name': 'id_vacancie', 'type': Integer},
                {'name': 'id_user', 'type': BigInteger},
                {'name': 'text', 'type': String(255)},
                {'name': 'data_sent', 'type': DateTime, 'default': func.now()}
            ]
        )

async def create_table_talent_pool(table_name="talent_pool"):
    async with db_manager as client:
        await client.create_table(
            table_name=table_name,
            columns=[
                {'name': 'id_user', 'type': BigInteger},
                {'name': 'location', 'type': String(255)},
                {'name': 'skill_tags', 'type': String(255)},
                {'name': 'experience_years', 'type': String(255)},
                {'name': 'data_sent', 'type': DateTime, 'default': func.now()}
            ]
        )

#insert table
async def insert_user(user_data: dict, table_name='users_reg'):
    query = text(f"""
        INSERT INTO {table_name} (user_id, full_name, user_login, date_reg) 
        VALUES (:user_id, :full_name, :user_login, :date_reg)
        ON CONFLICT (user_id) DO NOTHING;
    """)
    current_date = user_data.get('date_reg', datetime.now())
    
    async with db_manager.session() as session:
        try:
            await session.execute(query, {
                'user_id': user_data['user_id'],
                'full_name': user_data['full_name'],
                'user_login': user_data['user_login'],
                'date_reg': current_date
            })
            await session.commit()
        except Exception as e:
            logger.error(f"Error while writing user: {e}")

async def insert_data_review(data: dict, table_name="reviews"):
    skills_str = _parse_list_to_str(data.get('skills'))

    query = text(f"""
        INSERT INTO {table_name} (id_vacancie, id_user, status, location, work_mode, experience, skills)
        VALUES (:id_vacancie, :id_user, TRUE, :location, :work_mode, :experience, :skills)
    """)

    async with db_manager.session() as session:
        try:
            await session.execute(query, {
                'id_vacancie': int(data.get('id_vacancie')),
                'id_user': int(data.get('id_user')),
                'location': data.get('location'),
                'work_mode': data.get('work_mode'),
                'experience': data.get('experience'),
                'skills': skills_str
            })
            await session.commit()
        except Exception as e:
            logger.error(f"Error while writing review: {e}")

async def insert_data_for_hr_about_review(data: dict, table_name="for_hr_about_review"):
    skills_str = _parse_list_to_str(data.get('skills'))

    query = text(f"""
        INSERT INTO {table_name} (id_vacancie, id_user, location, work_mode, skills, experience, git_hub_url, status)
        VALUES (:id_vacancie, :id_user, :location, :work_mode, :skills, :experience, :git_hub_url, :status)
    """)

    async with db_manager.session() as session:
        try:
            await session.execute(query, {
                'id_vacancie': data.get('id_vacancy'),
                'id_user': data.get('id_user'),
                'location': data.get('location'),
                'work_mode': data.get('work_mode'),
                'skills': skills_str,
                'experience': data.get('experience'),
                'git_hub_url': data.get('github'),
                'status': data.get('status')
            })
            await session.commit()
        except Exception as e:
            logger.error(f"Error while writing HR review data: {e}")

async def insert_data_user_get_messages(data: dict, table_name="messages_to_user"):
    query = text(f"""
        INSERT INTO {table_name} (id_hr, id_vacancie, id_user, text)
        VALUES (:id_hr, :id_vacancie, :id_user, :text)
    """)
    async with db_manager.session() as session:
        try:
            await session.execute(query, {
                'id_hr': int(data['hr_id']),
                'id_vacancie': int(data['vacancy_id']),
                'id_user': int(data['user_id']),
                'text': data['comment']
            })
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting message to user: {e}")
            return False

async def insert_vacancies(data: dict, table_name='vacancie'):
    skills_str = _parse_list_to_str(data.get('skills'))
    nice_to_have_str = _parse_list_to_str(data.get('nice_to_have'))

    query = text(f"""
        INSERT INTO {table_name} (
            is_active, created_at, company_name, job_position, location, 
            work_mode, salary, currency, experience, skills, nice_to_have, more_about_it
        )
        VALUES (TRUE, NOW(), :company_name, :job_position, :location, :work_mode, 
                :salary, :currency, :experience, :skills, :nice_to_have, :more_about_it)
    """)

    async with db_manager.session() as session:
        try:
            await session.execute(query, {
                'company_name': data.get('company_name'),
                'job_position': data.get('job_position'),
                'location': data.get('location'),
                'work_mode': data.get('work_mode'),
                'salary': data.get('salary'),
                'currency': data.get('currency'),
                'experience': data.get('experience'),
                'skills': skills_str,
                'nice_to_have': nice_to_have_str,
                'more_about_it': data.get('more_about_it')
            })
            await session.commit()
            logger.debug("Vacancy successfully added to the database!")
        except Exception as e:
            logger.error(f"Error while writing a job: {e}")


#select table
async def select_user_data(user_id: int, table_name='users_reg'):
    async with db_manager as client:
        return await client.select_data(table_name=table_name, where_dict={'user_id': user_id}, one_dict=True)
    
async def select_all_users(table_name='users_reg', count=False):
    async with db_manager as client:
        all_users = await client.select_data(table_name=table_name)
        return len(all_users) if count else all_users

async def select_all_vacancies(table_name='vacancie'):
    async with db_manager as client:
        return await client.select_data(table_name=table_name)

async def select_search_vacancie(id_vacancy: int, table_name="vacancie"):
    if isinstance(id_vacancy, int):
        query = text(f"SELECT * FROM {table_name} WHERE id = :search_value")
        params = {"search_value": int(id_vacancy)}
    else:
        query = text(f"SELECT * FROM {table_name} WHERE job_position ILIKE :search_value")
        params = {"search_value": f"%{id_vacancy}%"}

    async with db_manager.session() as session:
        result = await session.execute(query, params)
        return [dict(v) for v in result.mappings().all()]

async def select_data_for_hr_about_review(id_vacancie, id_user, table_name="for_hr_about_review"):
    query = text(f"""
        SELECT id_vacancie, id_user, location, work_mode, experience, skills
        FROM {table_name}
        WHERE id_user = :id_user AND id_vacancie = :id_vacancie
    """)
    async with db_manager.session() as session:
        result = await session.execute(query, {
            'id_user': int(id_user), 
            'id_vacancie': int(id_vacancie)
        })
        row = result.mappings().first()
        return dict(row) if row else None

async def select_data_user_reviews(user_id: int, table_name="reviews"):
    # Оптимізовано JOIN (без касту типів ::integer, бо типи тепер узгоджені)
    query = text(f"""
        SELECT r.id_vacancie, r.status, v.company_name, v.job_position, v.salary, v.skills
        FROM {table_name} r
        INNER JOIN vacancie v ON r.id_vacancie = v.id  
        WHERE r.id_user = :id_user
    """)
    async with db_manager.session() as session:
        result = await session.execute(query, {'id_user': int(user_id)})
        return [dict(row) for row in result.mappings().all()]

async def select_data_all_reviews(table_name="for_hr_about_review"):
    query = text(f"""
        SELECT r.id_vacancie, r.status, r.location, r.work_mode, r.experience, r.id_user,
               v.company_name, v.job_position, r.skills, r.git_hub_url, u.full_name, u.user_login
        FROM {table_name} r
        LEFT JOIN vacancie v ON r.id_vacancie = v.id
        LEFT JOIN users_reg u ON r.id_user = u.user_id
        WHERE r.id_vacancie IS NOT NULL
          AND r.status = 'pending'
    """)
    async with db_manager.session() as session:
        result = await session.execute(query)
        return [dict(row) for row in result.mappings().all()]

async def select_data_user_get_messages(user_id: int, table_name="messages_to_user"):
    query = text(f"""
        SELECT m.id_hr, m.id_vacancie, m.id_user, m.text, v.company_name, v.job_position, v.skills
        FROM {table_name} m
        INNER JOIN vacancie v ON m.id_vacancie = v.id  
        WHERE m.id_user = :id_user
    """)
    async with db_manager.session() as session:
        result = await session.execute(query, {'id_user': int(user_id)})
        return [dict(row) for row in result.mappings().all()]


    skills_str = _parse_list_to_str(skills)
    query = text(f"""
        INSERT INTO {table_name} (id_user, location, skill_tags, experience_years)
        VALUES (:id_user, :location, :skill_tags, :experience_years)
    """)
    async with db_manager.session() as session:
        try:
            await session.execute(query, {
                'id_user': int(user_id),
                'location': location,
                'skill_tags': skills_str,
                'experience_years': experience
            })
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding to talent pool: {e}")
            return False

#update table 
async def update_user_status_as_false(user_id, vacancy_id, table_name="reviews"):
    query = text(f"""
        UPDATE {table_name}
        SET status = FALSE
        WHERE id_user = :id_user AND id_vacancie = :id_vacancie
    """)
    async with db_manager.session() as session:
        try:
            await session.execute(query, {'id_user': int(user_id), 'id_vacancie': int(vacancy_id)})
            await session.commit()
        except Exception as e:
            logger.error(f"Error updating status: {e}")
