import asyncio
from bot.create_bot import bot, dp, admins
from bot.db_handler.db_funk import create_table_users, create_table_vacancies, get_all_users

from bot.hendlers.admin_panel import admin_router
from bot.hendlers.user_router import user_router

from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.db_handler.db_funk import get_all_users


async def set_commands():
    commands = [BotCommand(command='start', description='Start'),
                BotCommand(command='profile', description='My profile')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

async def start_bot():
    await create_table_users()
    await create_table_vacancies()
    await set_commands()
    count_users = await get_all_users(count=True)

    try:
        for admin_id in admins:
            await bot.send_message(admin_id, f'I\'m online. Now in data base <b>{count_users}</b> reviews.')
    except:
        pass

async def stop_bot():
    try:
        for admin_id in admins:
            await bot.send_message(admin_id, 'Bot is stopped.')
    except:
        pass

async def main():
    for admin_id in admins:
        dp.include_router(admin_router)
    dp.include_router(user_router)

    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())