import telebot
from config import API_TOKEN
from database import init_db
from handlers import register_handlers

bot = telebot.TeleBot(API_TOKEN)

init_db()
register_handlers(bot)

bot.infinity_polling()
