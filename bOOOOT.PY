import asyncio
import json
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = "8990545849:AAFcPAP17gj-9Y_qCA0PqP6rESPZek7jXuc"
ADMIN_IDS = [36268309]

DB_NAME = "miner.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 5.0,
            ref_code TEXT UNIQUE,
            created_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bet REAL,
            win REAL,
            status TEXT,
            played_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 5.0

def add_balance(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cur.fetchone():
        conn.close()
        return
    cur.execute(
        "INSERT INTO users (user_id, username, ref_code, created_at) VALUES (?, ?, ?, ?)",
        (user_id, username, f"REF{user_id}", datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def save_game(user_id, bet, win, status):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO games (user_id, bet, win, status, played_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, bet, win, status, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(msg: types.Message):
    user_id = msg.from_user.id
    username = msg.from_user.username or "unknown"
    add_user(user_id, username)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть в мины", web_app=WebAppInfo(url="https://neymar228-design.github.io/Mines-game-bot/game.html"))],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
         InlineKeyboardButton(text="🔗 Рефералка", callback_data="referral")]
    ])

    await msg.answer(
        f"⛏️ Добро пожаловать в MineGame!\nБаланс: {get_balance(user_id)} GIFT",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data == "balance")
async def show_balance(callback: types.CallbackQuery):
    bal = get_balance(callback.from_user.id)
    await callback.message.edit_text(f"💰 Баланс: {bal} GIFT")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "referral")
async def show_referral(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    link = f"https://t.me/{bot.username}?start=REF{user_id}"
    await callback.message.edit_text(f"🔗 Твоя реферальная ссылка:\n`{link}`", parse_mode="Markdown")
    await callback.answer()

@dp.message(lambda msg: msg.web_app_data)
async def handle_game(msg: types.Message):
    data = json.loads(msg.web_app_data.data)
    user_id = msg.from_user.id
    bet = float(data.get("bet", 1.0))
    win = float(data.get("win", 0.0))

    if win > 0:
        add_balance(user_id, win)
        save_game(user_id, bet, win, "win")
        await msg.answer(f"🎉 Ты выиграл +{win} GIFT! Баланс: {get_balance(user_id)}")
    else:
        add_balance(user_id, -bet)
        save_game(user_id, bet, 0, "lose")
        await msg.answer(f"💥 Мина! Ты потерял {bet} GIFT. Баланс: {get_balance(user_id)}")

async def main():init_db()
    print("🟢 Бот с игрой запущен")
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
