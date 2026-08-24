import asyncio
import logging
import os
import aiohttp
import feedparser
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Configure Logging
logging.basicConfig(level=logging.INFO)

# Load configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")  # e.g., @YourChannelName
POST_INTERVAL = int(os.getenv("POST_INTERVAL", "600"))  # Seconds (default: 10 mins)

# Sports RSS Feed (Default: BBC Sports)
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "http://feeds.bbci.co.uk/sport/rss.xml")

# Prevent duplicate posts
seen_links = set()

# Initialize Bot & Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👋 **Welcome to SportSphere Global!**\n\n"
        "Global sports news, live match updates, and real-time scores in multiple languages.\n\n"
        "**Channel Auto-Poster Status:**\n"
        f"• Target Channel: `{TARGET_CHANNEL or 'Not Configured'}`\n"
        f"• Check Interval: `{POST_INTERVAL} seconds`\n\n"
        "To enable auto-posting:\n"
        "1. Add this bot as an **Admin** in your channel with **Post Messages** permissions.\n"
        "2. Set your `TARGET_CHANNEL` environment variable on Railway.",
        parse_mode="Markdown"
    )

async def fetch_rss():
    """Fetches the latest news item asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(RSS_FEED_URL) as response:
            if response.status == 200:
                content = await response.text()
                return feedparser.parse(content)
            return None

async def auto_post_loop():
    """Background task that runs continuously to fetch and post news."""
    while True:
        try:
            if TARGET_CHANNEL:
                feed = await fetch_rss()
                if feed and feed.entries:
                    latest = feed.entries[0]
                    link = latest.link

                    if link not in seen_links:
                        seen_links.add(link)
                        
                        title = latest.title
                        summary = latest.summary[:200] + "..." if len(latest.summary) > 200 else latest.summary
                        
                        caption = (
                            f"🏆 **SportSphere Global**\n\n"
                            f"📌 **{title}**\n\n"
                            f"{summary}\n\n"
                            f"🌍 _Coverage by @SportSphereGlobal_bot_"
                        )
                        
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="📖 Read Full Story", url=link)]
                            ]
                        )

                        await bot.send_message(
                            chat_id=TARGET_CHANNEL,
                            text=caption,
                            parse_mode="Markdown",
                            reply_markup=keyboard
                        )
                        logging.info(f"Posted article: {title}")

        except Exception as e:
            logging.error(f"Auto-post error: {e}")

        await asyncio.sleep(POST_INTERVAL)

async def main():
    # Start auto-posting background loop
    asyncio.create_task(auto_post_loop())
    
    # Start bot polling
    logging.info("Starting @SportSphereGlobal_bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())