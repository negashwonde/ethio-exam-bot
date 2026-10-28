import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
import os
import pandas as pd
from flask import Flask
from threading import Thread

# 1. ዌብ ሰርቨር (Flask) ማዋቀር - Render የ ፖርት ጥያቄን እንዲቀበል
app = Flask("")


@app.route("/")
def home():
  return "🤖 CS Exit Exam Bot is running live and active!"


def run_flask():
  # Render የሚሰጠውን Port በራስ-ሰር እንዲወስድ ማድረግ
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


# 2. የቴሌግራም ቦት ማዋቀር
TOKEN = "8989053444:AAGi6glRFJ4Besq0yvTEJGm2YakJgYnjKdw"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_NAME = "brand_new_exam.db"


# ዳታቤዙን በራስ-ሰር ማቀናጀት
def init_and_load_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            exam_year TEXT,
            question_text TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_answer TEXT,
            explanation TEXT
        )
    """
  )
  conn.commit()
  conn.close()


# /start ትዕዛዝ - ዋናው ሜኑ
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  user_name = message.from_user.first_name

  builder = InlineKeyboardBuilder()
  builder.row(
      types.InlineKeyboardButton(
          text="📅 2018 Exit Exam", callback_data="exam_2018"
      )
  )

  await message.answer(
      f"👋 **ሰላም {user_name}!**\n\n"
      f"🎓 **ወደ ኮምፒውተር ሳይንስ Exit Exam ዝግጅት ቦት እንኳን ደህና መጡ።**\n\n"
      f"👇 ከታች ያለውን በመጫን የ 2018 ፈተና ይጀምሩ:",
      reply_markup=builder.as_markup(),
      parse_mode="Markdown",
  )


# ፈተና መጀመሪያ
@dp.callback_query(F.data == "exam_2018")
async def start_2018_exam(callback: types.CallbackQuery):
  await callback.answer()

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, question_text, option_a, option_b, option_c, option_d FROM"
      " questions WHERE exam_year = '2018' LIMIT 1"
  )
  q = cursor.fetchone()
  conn.close()

  if q:
    q_id, q_text, opt_a, opt_b, opt_c, opt_d = q

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=f"A) {opt_a}", callback_data=f"ans_{q_id}_A"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text=f"B) {opt_b}", callback_data=f"ans_{q_id}_B"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text=f"C) {opt_c}", callback_data=f"ans_{q_id}_C"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text=f"D) {opt_d}", callback_data=f"ans_{q_id}_D"
        )
    )

    await callback.message.answer(
        f"📝 **2018 Exit Exam - Question 1:**\n\n{q_text}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
  else:
    await callback.message.answer(
        "⚠️ በዳታቤዙ ውስጥ 2018 ዓመተ ምህረት ጥያቄዎች አልተገኙም!"
    )


# መልስ ማረጋገጫ
@dp.callback_query(F.data.startswith("ans_"))
async def check_answer(callback: types.CallbackQuery):
  await callback.answer()

  parts = callback.data.split("_")
  q_id = parts[1]
  chosen_opt = parts[2]

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT correct_answer, explanation FROM questions WHERE id = ?", (q_id,)
  )
  res = cursor.fetchone()
  conn.close()

  if res:
    correct, explanation = res

    if chosen_opt == correct:
      result_text = "✅ **ትክክል ነው! (Correct)**"
    else:
      result_text = f"❌ **ስህተት ነው። ትክክለኛው መልስ: {correct}**"

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="➡️ Next Question (ቀጣይ)", callback_data=f"next_{q_id}"
        )
    )

    feedback = (
        f"{result_text}\n\n"
        f"💡 **ማብራሪያ (Explanation):**\n{explanation}"
    )

    await callback.message.answer(
        feedback, reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


# ቀጣይ ጥያቄ
@dp.callback_query(F.data.startswith("next_"))
async def next_question(callback: types.CallbackQuery):
  await callback.answer()

  current_id = int(callback.data.split("_")[1])

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, question_text, option_a, option_b, option_c, option_d FROM"
      " questions WHERE id > ? AND exam_year = '2018' ORDER BY id ASC LIMIT 1",
      (current_id,),
  )
  q = cursor.fetchone()
  conn.close()

  if q:
    q_id, q_text, opt_a, opt_b, opt_c, opt_d = q

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=f"A) {opt_a}", callback_data=f"ans_{q_id}_A"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text=f"B) {opt_b}", callback_data=f"ans_{q_id}_B"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text=f"C) {opt_c}", callback_data=f"ans_{q_id}_C"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text=f"D) {opt_d}", callback_data=f"ans_{q_id}_D"
        )
    )

    await callback.message.answer(
        f"📝 **2018 Exit Exam - Next Question:**\n\n{q_text}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
  else:
    await callback.message.answer(
        "🎉 **እንኳን ደስ አለዎት!** የ 2018 ጥያቄዎችን በሙሉ አጠናቀዋል።",
        reply_markup=InlineKeyboardBuilder()
        .row(
            types.InlineKeyboardButton(
                text="🏠 Main Menu", callback_data="back_menu"
            )
        )
        .as_markup(),
    )


@dp.callback_query(F.data == "back_menu")
async def back_to_menu(callback: types.CallbackQuery):
  await callback.message.delete()
  await cmd_start(callback.message)
  await callback.answer()


async def main():
  init_and_load_db()

  # Flask ሰርቨርን ከድብቅ ባክግራውንድ (Background Thread) ማስጀመር
  flask_thread = Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()
  print("🌐 Flask Web Server started successfully on port 8080")

  print("🚀 Bot is running and successfully connected with SQLite!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())