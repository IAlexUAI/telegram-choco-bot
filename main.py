import os
import csv
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
ORDERS_FILE = os.path.join(os.path.dirname(__file__), "orders.csv")

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.info(f"✅ Запуск бота...\n📁 Файл заказов: {ORDERS_FILE}")

user_states = {}
user_carts = {}

ITEMS = {
    "Classic Milk Bomb": "11.00",
    "Dark Mint": "12.00",
    "White Raspberry": "13.00",
    "Salted Caramel": "12.00",
    "Minty Cool Bomb": "12.00",
    "Berry Blast": "13.00",
    "Citrus Dream": "12.00",
    "Caramel Swirl": "12.00",
    "Набор 4 шт.": "48.00",
    "Набор 6 шт.": "65.00",
    "Упаковка (+2 шт)": "2.00"
}

main_menu = ReplyKeyboardMarkup([["🍫 Каталог", "🛒 Корзина"], ["📋 Помощь"]], resize_keyboard=True)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_carts[user.id] = []
    await update.message.reply_text(
        "Привет! Я бот для заказа шоколадных бомбочек. Выбери действие:", reply_markup=main_menu
    )

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "🍫 Каталог":
        catalog = "\n".join([f"{name}: {price}₽" for name, price in ITEMS.items()])
        await update.message.reply_text(f"🛍 Наш каталог:\n\n{catalog}")
    elif text in ITEMS:
        cart = user_carts.setdefault(user_id, [])
        cart.append(text)
        await update.message.reply_text(f"✅ Товар \"{text}\" добавлен в корзину.")
    elif text == "🛒 Корзина":
        cart = user_carts.get(user_id, [])
        if not cart:
            await update.message.reply_text("🧺 Ваша корзина пуста.")
        else:
            summary = "\n".join(cart)
            total = sum(float(ITEMS[item]) for item in cart)
            await update.message.reply_text(f"🧾 Ваша корзина:\n{summary}\n\nИтого: {total}₽")
    elif text == "📋 Помощь":
        await update.message.reply_text("❓ Чтобы заказать, нажми «Каталог», выбери товар и смотри корзину.")
    else:
        await update.message.reply_text("❌ Неизвестная команда. Выбери из меню.")

# Запуск
if __name__ == '__main__':
    import asyncio

    async def main():
        application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .build()
        )

        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        await application.run_polling()

    asyncio.run(main())