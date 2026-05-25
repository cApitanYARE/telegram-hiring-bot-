import logging

import asyncio
import os
from decouple import config
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram.fsm.storage.memory import MemoryStorage

from asyncpg_lite import DatabaseManager

import redis
from aiogram.fsm.storage.redis import RedisStorage


load_dotenv()

#pg_db = PostgresHandler(config('PG_LINK'))

admins = [int(admin_id) for admin_id in config('ADMINS').split(',')]

redis_fsm = redis.Redis(host='localhost', port=6379, decode_responses=True)
storage = RedisStorage(redis=redis_fsm)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

db_manager = DatabaseManager(db_url=config('DATABASE_URL'), deletion_password=config('ROOT_PASS'))

bot = Bot(token=config('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()
#storage=storage


