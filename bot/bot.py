#!/usr/bin/env python3
"""
Telegram bot entry point.

Supports two modes:
- Test mode: `uv run bot.py --test "message"` prints response to stdout
- Telegram mode: `uv run bot.py` connects to Telegram and handles messages
"""

import argparse
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import ReplyKeyboardMarkup

from handlers import (
    get_handler,
    get_main_keyboard,
    get_help_text,
)
from services.llm_client import route
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_test_mode(message: str) -> None:
    """
    Run a message through the bot and print result to stdout.

    Supports both slash commands and natural language queries.
    - Slash commands (e.g., /start, /help) are handled by command handlers
    - Natural language queries are routed through the LLM
    """
    message = message.strip()

    # Check if it's a slash command
    if message.startswith("/"):
        parts = message.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        handler = get_handler(cmd)
        if handler is None:
            print(f"Unknown command: {cmd}. Use /help to see available commands.")
            sys.exit(0)

        # Call handler - some take arguments, some don't
        if cmd == "/scores":
            response = handler(arg)
        else:
            response = handler()

        print(response)
        sys.exit(0)
    else:
        # Natural language query - route through LLM
        response = route(message)
        print(response)
        sys.exit(0)


async def handle_start_command(message: types.Message) -> None:
    """Handle /start command."""
    handler = get_handler("/start")
    if handler:
        keyboard = get_main_keyboard()
        await message.answer(
            handler(),
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


async def handle_help_command(message: types.Message) -> None:
    """Handle /help command."""
    handler = get_handler("/help")
    if handler:
        keyboard = get_main_keyboard()
        await message.answer(
            handler(),
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


async def handle_health_command(message: types.Message) -> None:
    """Handle /health command."""
    handler = get_handler("/health")
    if handler:
        response = handler()
        await message.answer(response)


async def handle_labs_command(message: types.Message) -> None:
    """Handle /labs command."""
    handler = get_handler("/labs")
    if handler:
        response = handler()
        await message.answer(response)


async def handle_scores_command(message: types.Message, command: Command.CommandObj) -> None:
    """Handle /scores command with optional argument."""
    handler = get_handler("/scores")
    if handler:
        arg = command.args.strip() if command.args else ""
        response = handler(arg)
        await message.answer(response)


async def handle_text_message(message: types.Message) -> None:
    """Handle plain text messages through LLM routing."""
    user_text = message.text or ""
    
    # Show typing indicator
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Route through LLM
    response = route(user_text)
    
    if response:
        await message.answer(response, parse_mode="Markdown")


async def run_telegram_mode() -> None:
    """Run the bot in Telegram mode."""
    config = load_config()
    
    bot_token = config.get("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN is not configured. Set it in .env.bot.secret or environment.")
        sys.exit(1)
    
    # Create bot and dispatcher
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    
    # Register command handlers
    dp.message.register(handle_start_command, CommandStart())
    dp.message.register(handle_help_command, Command("help"))
    dp.message.register(handle_health_command, Command("health"))
    dp.message.register(handle_labs_command, Command("labs"))
    dp.message.register(handle_scores_command, Command("scores"))
    
    # Register text message handler (for natural language queries)
    dp.message.register(handle_text_message)
    
    logger.info("Application started. Bot is polling for messages...")
    
    # Start polling
    await dp.start_polling(bot)


def main():
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        type=str,
        metavar="COMMAND",
        help="Test mode: run a command and print response to stdout"
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_test_mode(args.test)
        return
    
    # Telegram mode
    try:
        asyncio.run(run_telegram_mode())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
