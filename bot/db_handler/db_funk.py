import asyncio
import asyncpg
from decouple import config
from sqlalchemy import BigInteger, Integer, String, DateTime, Boolean, Text, DateTime, text, Identity, select
from sqlalchemy.sql import func
from bot.create_bot import db_manager
from sqlalchemy.ext.asyncio import AsyncSession


DATABASE_URL = config('DATABASE_URL')

async def create_table_users(table_name='users_reg'):
    async with db_manager as client:
        await client.create_table(table_name=table_name,
                                columns=[
                                    {
                                        'name': 'user_id',
                                        'type': BigInteger,  
                                        'primary_key': True,
                                        'autoincrement': True  
                                    },
                                    {
                                        'name': 'full_name',
                                        'type': String(255)  
                                    },
                                    {
                                        'name': 'user_login',
                                        'type': String(255)  
                                    },
                                    {
                                        'name': 'date_reg',
                                        'type': DateTime,  
                                        'default': func.now()
                                    }
                                ])

try:
    asyncio.get_event_loop().create_task(create_table_users())
except RuntimeError:
    pass

async def get_user_data(user_id: int, table_name='users_reg'):
    async with db_manager as client:
        return await client.select_data(table_name=table_name, where_dict={'user_id': user_id}, one_dict=True)

async def get_all_users(table_name='users_reg', count=False):
    async with db_manager as client:
        all_users = await client.select_data(table_name=table_name)
        return len(all_users) if count else all_users

async def insert_user(user_data: dict, table_name='users_reg'):
    from datetime import datetime
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)
    try:
        # Тепер у нас 4 колонки і 4 параметри ($1, $2, $3, $4)
        # Виправлено назву колонки з data_reg на date_reg відповідно до ваших логів
        query = f"""
        INSERT INTO {table_name} (user_id, full_name, user_login, date_reg) 
        VALUES ($1, $2, $3, $4);
        """
        
        # Генеруємо поточну дату прямо тут, якщо її не передали
        current_date = user_data.get('date_reg', datetime.now())

        await conn.execute(
            query, 
            user_data['user_id'], 
            user_data['full_name'], 
            user_data['user_login'], 
            current_date
        )
    except asyncpg.exceptions.UniqueViolationError:
        pass  # Користувач вже є, ігноруємо
    except Exception as e:
        print(f"Error while writing user: {e}")
    finally:
        await conn.close()

async def create_table_vacancies(table_name='vacancie'):

    async with db_manager as client:
        await client.create_table(table_name=table_name,
                                    columns=[
                                        {
                                            'name': 'id',
                                            'type': Integer,              
                                            'primary_key': True,     
                                            'autoincrement': True
                                        },
                                        {
                                            'name' : 'is_active',
                                            'type': Boolean,
                                            'server_default': text('true')
                                        },
                                        {
                                            'name': 'created_at',
                                            'type': DateTime,  
                                            'server_default': text('NOW()')
                                        },
                                        {
                                            'name': 'company_name',
                                            'type': String(255)
                                        },
                                        {
                                            'name' : 'job_position',
                                            'type': String(255)
                                        },
                                        {
                                            'name': 'location',
                                            'type': String(255)
                                        },
                                        {
                                            'name' : 'work_mode',
                                            'type': String(255) 
                                        },
                                        {
                                            'name' : 'salary',
                                            'type': String(255)
                                        },
                                        {
                                            'name': 'currency',
                                            'type': String(10)  
                                        },
                                        {
                                            'name' : 'experience',
                                            'type': String(255)
                                        },
                                        {
                                            'name' : 'skills',
                                            'type': String(255)
                                        },
                                        { 
                                            'name' : 'nice_to_have',
                                            'type': String(255), 
                                        },
                                        {
                                            'name' : 'more_about_it',
                                            'type' : Text
                                        }
                                    ])

async def add_vacancies(data: dict,table_name='vacancie'):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    skills = data.get('skills')
    if isinstance(skills, list):
        skills_str = ", ".join(str(s) for s in skills)
    else:
        skills_str = str(skills) if skills else None

    nice_to_have = data.get('nice_to_have')
    if isinstance(nice_to_have, list):
        nice_to_have_str = ", ".join(str(n) for n in nice_to_have)
    else:
        nice_to_have_str = str(nice_to_have) if nice_to_have else None

    try:
        query = f"""
        INSERT INTO {table_name} (
            is_active, created_at, 
            company_name, job_position, location, work_mode, 
            salary, currency, experience, skills, nice_to_have, more_about_it
        )
        VALUES (TRUE, NOW(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10) 
        """
        await conn.execute(
            query, 
            data.get('company_name'), 
            data.get('job_position'), 
            data.get('location'), 
            data.get('work_mode'), 
            data.get('salary'), 
            data.get('currency'), 
            data.get('experience'), 
            skills_str, 
            nice_to_have_str, 
            data.get('more_about_it')
        )
        print("--- DEBUG: vacancies successfully added to the database ! ---")
        
    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

async def get_all_vacancies(table_name='vacancie'):

    async with db_manager as client:
        all_vacancies = await client.select_data(table_name=table_name)
        return all_vacancies

async def search_vacancie(data, table_name="vacancie"):
    
    if data.isdigit():
        query = text(f"SELECT * FROM {table_name} WHERE id = :search_value")
        value = int(data)
    else:
        query = text(f"SELECT * FROM {table_name} WHERE job_position ILIKE :search_value")
        value = f"%{data}%"

    async with db_manager.session() as session:
        result = await session.execute(query, {"search_value": value})
        vacancies = result.mappings().all()
        return [dict(v) for v in vacancies]

async def create_table_reviews(table_name="reviews"):
    async with db_manager as client:
        await client.create_table(table_name=table_name,
        columns=[
            {
                'name' : 'id_vacancie',
                'type': String(255),
            },
            {
                'name' : 'id_user',
                'type': String(255)
            },
            {
                'name' : 'status',
                'type': Boolean,
                'default': True
            },
            {
                'name' : 'location',
                'type': String(255)
            },
            {
                'name' : 'work_mode',
                'type': String(255)
            },
            {
                'name' : 'experience',
                'type': String(255)
            },
            {
                'name' : 'skills',
                'type': String(255)
            },
            {
                'name' : 'data_sent',
                'type': DateTime(),
                'default': func.now()
            }
        ])

async def insert_data_review(data: dict,table_name="reviews"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    skills = data.get('skills')
    if isinstance(skills, list):
        skills_str = ", ".join(str(s) for s in skills)
    else:
        skills_str = str(skills) if skills else None

    try:
        query = f"""
        INSERT INTO {table_name} (
            id_vacancie, id_user, status, location, work_mode, experience, skills
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await conn.execute(
            query, 
            data.get('id_vacancie'),  
            data.get('id_user'),
            True,      
            data.get('location'),     
            data.get('work_mode'),   
            data.get('experience'),   
            skills_str,               
        )
        print("--- DEBUG: vacancies successfully added to the database ! ---")
        
    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

async def create_table_for_hr_about_review(table_name="for_hr_about_review"):
    async with db_manager as client:
        await client.create_table(table_name=table_name,
        columns=[
            {
                'name' : 'id_vacancie',
                'type': String(255),
            },
            {
                'name' : 'id_user',
                'type': String(255)
            },
            {
                'name' : 'location',
                'type': String(255)
            },
            {
                'name' : 'work_mode',
                'type': String(255)
            },
            {
                'name' : 'skills',
                'type': String(255)
            },
            {
                'name' : 'experience',
                'type': String(255)
            },
            {
                'name' : 'git_hub_url',
                'type': String(255)
            },
        ])

async def insert_data_for_hr_about_review(data: dict,table_name="for_hr_about_review"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    skills = data.get('skills')
    if isinstance(skills, list):
        skills_str = ", ".join(str(s) for s in skills)
    else:
        skills_str = str(skills) if skills else None

    try:
        query = f"""
        INSERT INTO {table_name} (
            id_vacancie, id_user, location, work_mode, skills, experience, git_hub_url
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await conn.execute(
            query, 
            data.get('id_vacancy'),  
            data.get('id_user'),   
            data.get('location'),     
            data.get('work_mode'),
            skills_str,   
            data.get('experience'),
            data.get('git_hub'),                    
        )
        print("--- DEBUG: vacancies successfully added to the database ! ---")
        
    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

async def select_data_for_hr_about_review(id_vacancie, id_user,table_name="for_hr_about_review"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    try:
        query = f"""
        SELECT
            id_vacancie,
            id_user,
            location,
            work_mode,
            experience,
            skills
        FROM {table_name}
        WHERE id_user = $1 AND id_vacancie = $2
        """
        data_review = await conn.fetchrow(query, str(id_user),str(id_vacancie))

        if data_review:
            return dict(data_review)
        return None


    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

async def get_data_user_reviews(data: int,table_name="reviews"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    try:
        query = f"""
        SELECT
            r.id_vacancie,
            r.status,
            v.company_name,
            v.job_position,
            v.salary,
            v.skills
        FROM {table_name} r
        INNER JOIN vacancie v ON r.id_vacancie::integer = v.id  
        WHERE r.id_user = $1
        """
        data_review = await conn.fetch(query, str(data))
        return data_review
        
    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

async def get_data_all_reviews(table_name="reviews"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    try:
        query = f"""
        SELECT
            r.id_vacancie,
            r.status,
            r.location,
            r.work_mode,
            r.experience,
            r.id_user,
            v.company_name,
            v.job_position,
            r.skills,
            u.full_name,
            u.user_login
        FROM {table_name} r
        LEFT JOIN vacancie v ON NULLIF(r.id_vacancie, 'None')::integer = v.id
        LEFT JOIN users_reg u ON NULLIF(r.id_user, 'None')::integer = u.user_id
        WHERE r.id_vacancie IS NOT NULL
          AND r.id_vacancie != 'None'
          AND r.status != 'false'
        """
        data_review = await conn.fetch(query)
        return data_review
        
    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

async def set_user_status_as_false(user, vacancy,table_name="reviews"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    try:
        query = f"""
        UPDATE {table_name}
        SET status = 'false'
        WHERE id_user = $1 AND id_vacancie = $2
        """
        data_review = await conn.execute(query,user,vacancy)
        return data_review

    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

async def create_table_messeges_to_user(table_name="messages_to_user"):
    async with db_manager as client:
        await client.create_table(table_name=table_name,
        columns=[
            {
                'name' : 'id_hr',
                'type': Integer
            },
            {
                'name' : 'id_vacancie',
                'type': Integer
            },
            {
                'name' : 'id_user',
                'type': Integer
            },
            {
                'name' : 'text',
                'type': String(255)
            },
            {
                'name' : 'data_sent',
                'type': DateTime(),
                'default': func.now()
            }
        ])

async def insert_data_user_get_messages(data: dict,table_name="messages_to_user"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    try:
        query = f"""
        INSERT INTO {table_name} (id_hr, id_vacancie, id_user, text)
        VALUES ($1, $2, $3, $4)
        """
        await conn.execute(
            query, 
            data['hr_id'],
            data['vacancy_id'],
            data['user_id'],
            data['comment'],
        )

        return True
        
    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

#user get answeared by HR
async def get_data_user_get_messages(data: int,table_name="messages_to_user"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    try:
        query = f"""
        SELECT
            m.id_hr,
            m.id_vacancie,
            m.id_user,
            m.text,
            v.company_name,
            v.job_position,
            v.skills
        FROM {table_name} m
        INNER JOIN vacancie v ON m.id_vacancie::integer = v.id  
        WHERE m.id_user = $1
        """
        data_review = await conn.fetch(query, int(data))
        return data_review
        
    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()

async def create_table_talent_pool(table_name="talent_pool"):
    async with db_manager as client:
        await client.create_table(table_name=table_name,
        columns=[
            {
                'name' : 'id_user',
                'type': Integer
            },
            {
                'name' : 'location',
                'type': String(255)
            },
            {
                'name' : 'skill_tags',
                'type': String(255)
            },
            {
                'name' : 'experience_years',
                'type': String(255)
            },
            {
                'name' : 'data_sent',
                'type': DateTime(),
                'default': func.now()
            }
        ])

async def set_user_status_as_false(user, vacancy,table_name="reviews"):
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)

    try:
        query = f"""
        INSERT INTO {table_name} (id_user, location, skill_tags, experience_years)
        VALUES ($1, $2, $3, $4)
        """
        await conn.execute(
            query, 
            user,
            location,
            skills,
            experience,
        )

        return True
        
    except asyncpg.exceptions.UniqueViolationError:
        print("--- DEBUG: This vacancy already exists. (UniqueViolationError) ---")
    except Exception as e:
        print(f"Error while writing a job: {e}")
    finally:
        await conn.close()
