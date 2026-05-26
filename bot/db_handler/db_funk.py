import asyncio
import asyncpg
from decouple import config
from sqlalchemy import BigInteger, Integer, String, DateTime, Boolean, Text, DateTime, func
from bot.create_bot import db_manager

DATABASE_URL = config('DATABASE_URL')

async def create_table_users(table_name='users_reg'):
    async with db_manager as client:
        await client.create_table(table_name=table_name,
                                columns=[
                                    {
                                        'name': 'user_id',
                                        'type': BigInteger,  
                                        'primary_key': True
                                    },
                                    {
                                        'name': 'full_name',
                                        'type': String(255)  
                                    },
                                    {
                                        'name': 'user_login',
                                        'type': String(255)  
                                    },
                                    #{
                                     #   'name': 'date_reg',
                                    #    'type': 'TIMESTAMP',  
                                    #    'server_default': 'NOW()'
                                   # }
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
    clean_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(clean_url)
    try:
        query = f"""
        INSERT INTO {table_name} (user_id, full_name, user_login, data_reg) 
        VALUES ($1, $2, $3);
        """
        await conn.execute(query, user_data['user_id'], user_data['full_name'], user_data['user_login'], user_data['date_reg'])
    except asyncpg.exceptions.UniqueViolationError:
        pass
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
                                            'type': Boolean
                                        },
                                    #    {
                                     #       'name' : 'created_at',
                                    #        'type': func.now() 
                                      #  },
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
            company_name, job_position, location, work_mode, 
            salary, currency, experience, skills, nice_to_have, more_about_it
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
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

async def create_table_reviews(table_name="reviews"):
    async with db_manager as client:
        await client.create_table(table_name=table_name,
        columns=[
            {
                'name' : 'id_vacancie',
                'type': String(255)
            },
            {
                'name' : 'id_user',
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
            id_vacancie, id_user, location, work_mode, experience, skills
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await conn.execute(
            query, 
            data.get('id_vacancie'),  
            data.get('id_user'),      
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