import asyncio
from bot.create_bot import bot, dp, admins
from bot.db_handler.db_funk import create_table_users, create_table_vacancies, select_search_vacancie, create_table_messeges_to_user, create_table_talent_pool, create_table_for_hr_about_review

from bot.hendlers.admin_panel import admin_router
from bot.hendlers.user_router import user_router

from aiogram.types import BotCommand, BotCommandScopeDefault

from aiogram.exceptions import TelegramBadRequest


async def set_commands():
    commands = [BotCommand(command='start', description='Start'),
                BotCommand(command='profile', description='My profile')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

async def set_bot_description():
    await bot.set_my_description(
        description=(
            "Hello! This bot will help you find current vacancies, "
            "pass the initial interview and automatically send your resume to the HR manager. 🚀\n\n"
            "Press /start to begin!"
        )
    )

async def start_bot():
    try:
        await create_table_users()
        await create_table_vacancies()
        await create_table_for_hr_about_review()
        await create_table_messeges_to_user()
        await create_table_talent_pool()
    except Exception as e:
        await bot.send_message(f"Error creating database table: {e}")

    await set_commands()
    await set_bot_description()

    count_users = await select_search_vacancie(count=True)
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, f'I\'m online. Now in data base <b>{count_users}</b> reviews.')
        except Exception as e:
            print(f" Error: Admin {admin_id} didn't launch the bot or ID is wrong. Details: {e}")

async def stop_bot():
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, 'Bot is stopped.')
        except Exception as e:
            print(f" Error: Admin {admin_id} didn't launch the bot or ID is wrong. Details: {e}")

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