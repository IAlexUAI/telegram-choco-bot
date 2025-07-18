import os
import csv
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
ORDERS_FILE = os.path.join(os.path.dirname(__file__), "orders.csv")
logging.info(f"✅ Запуск бота...\nФайл заказов: {ORDERS_FILE}")

user_states = {}
user_carts = {}

ITEMS = {
    "Classic Milk Bomb": "11.00", "Dark Mint": "12.00", "White Raspberry": "13.00",
    "Salted Caramel": "12.00", "Minty Cool Bomb": "12.00", "Berry Blast": "13.00",
    "Citrus Dream": "12.00", "Caramel Swirl": "12.00",
    "Набор 4 шт.": "45.00", "Набор 6 шт.": "65.00", "Упаковка (+2 zł)": "2.00"
}

main_menu = ReplyKeyboardMarkup([["🍫 Каталог", "🛒 Корзина"], ["ℹ️ Помощь"]], resize_keyboard=True)

catalog_keyboard = ReplyKeyboardMarkup(
    [
        ["Classic Milk Bomb", "Dark Mint"],
        ["White Raspberry", "Salted Caramel"],
        ["Minty Cool Bomb", "Berry Blast"],
        ["Citrus Dream", "Caramel Swirl"],
        ["Набор 4 шт.", "Набор 6 шт."],
        ["Упаковка (+2 zł)"],
        ["🧾 Завершить заказ", "🔙 Назад"]
    ], resize_keyboard=True
)

CATALOG_TEXT = """🍫 <b>КЛАССИЧЕСКАЯ ЛИНЕЙКА</b>
🥛 Classic Milk Bomb — 11,00 zł
🌿 Dark Mint — 12,00 zł
🍫🍓 White Raspberry — 13,00 zł
🍬🧂 Salted Caramel — 12,00 zł

🧊 <b>ЛЕТНЯЯ ЛИНЕЙКА</b>
🌱❄️ Minty Cool Bomb — 12,00 zł
🍓🫐 Berry Blast — 13,00 zł
🍊🍋 Citrus Dream — 12,00 zł
🍯🧂 Caramel Swirl — 12,00 zł

🎁 <b>НАБОРЫ</b>
Набор 4 шт. — 45,00 zł (ассорти)
Набор 6 шт. — 65,00 zł (подарочный микс)
📦 Упаковка (по желанию) — +2 zł"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в бот шоколадных бомбочек! 🍫\nВыберите действие:", reply_markup=main_menu)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    full_name = update.message.from_user.full_name
    text = update.message.text.strip()

    if text == "🔙 Назад":
        await update.message.reply_text("Вы вернулись в меню.", reply_markup=main_menu)
        user_states[user_id] = None
        return

    if text == "🍫 Каталог":
        await update.message.reply_text(CATALOG_TEXT, parse_mode="HTML")
        await update.message.reply_text("📋 Выберите товар для добавления в корзину:", reply_markup=catalog_keyboard)
        return

    if text == "🛒 Корзина":
        cart = user_carts.get(user_id, [])
        if not cart:
            await update.message.reply_text("🧺 Ваша корзина пуста.")
        else:
            cart_text = format_cart(cart)
            total = calculate_total(cart)
            await update.message.reply_text(f"🧾 Ваш заказ:\n{cart_text}\n\n💰 <b>Итого: {total} zł</b>", parse_mode="HTML")
        return

    if text == "🧾 Завершить заказ":
        cart = user_carts.get(user_id, [])
        if not cart:
            await update.message.reply_text("❗️ Сначала добавьте товары.")
            return
        user_states[user_id] = "awaiting_info"
        await update.message.reply_text("✏️ Введите данные: ФИО, адрес, телефон.")
        return

    if text == "ℹ️ Помощь":
        await update.message.reply_text("📦 Доставка по всей Польше.\n💳 Оплата не требуется.\n📨 Вопросы: @ваш_менеджер")
        return

    if user_states.get(user_id) == "awaiting_info":
        cart = user_carts.get(user_id, [])
        cart_text = ", ".join(cart)
        total = calculate_total(cart)
        with open(ORDERS_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([full_name, user_id, text, cart_text, total])
        if ADMIN_CHAT_ID:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=f"📥 <b>Новый заказ от {full_name}:</b>\n\n🧾 <b>Заказ:</b> {cart_text}\n💰 <b>Сумма:</b> {total} zł\n📇 <b>Данные:</b> {text}\n\n<a href='tg://user?id={user_id}'>📲 Связаться</a>",
                parse_mode="HTML"
            )
        await update.message.reply_text("🎉 Спасибо за заказ! Мы скоро свяжемся с вами.", reply_markup=main_menu)
        user_states[user_id] = None
        user_carts[user_id] = []
        return

    if text in ITEMS:
        user_carts.setdefault(user_id, []).append(text)
        await update.message.reply_text(f"🛒 Добавлено в корзину: {text}")
        return

    await update.message.reply_text("Пожалуйста, выберите действие из меню.")

def format_cart(cart):
    lines = []
    for item in set(cart):
        qty = cart.count(item)
        price = float(ITEMS.get(item, "0"))
        total = qty * price
        lines.append(f"{item} x{qty} — {total:.2f} zł")
    return "\n".join(lines)

def calculate_total(cart):
    return f"{sum(float(ITEMS.get(i, 0)) for i in cart):.2f}"

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()