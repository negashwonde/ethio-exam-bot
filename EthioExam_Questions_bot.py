import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
import os
from flask import Flask
from threading import Thread

# 1. ዌብ ሰርቨር (Flask) ማዋቀር - Render የ ፖርት ጥያቄን እንዲቀበል
app = Flask("")


@app.route("/")
def home():
    return "🤖 WanK CS Exit Exam Bot is running live and active!"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# 2. የቴሌግራም ቦት ማዋቀር
TOKEN = "8523290430:AAGsDLx5iBkYrkCH1JW2QlG2wpbN-O0Omw4"
ADMIN_ID = 7806847963  # የእርስዎ የአድሚን ቴሌግራም ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_NAME = "brand_new_exam.db"


# ዳታቤዙን እና የተጠቃሚዎችን የፍተሻ/ክፍያ ሁኔታ መቆጣጠሪያ ሠንጠረዥ ማቀናጀት
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ዋናው የጥያቄዎች ሠንጠረዥ
    cursor.execute("""
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
    """)

    # የተጠቃሚዎችን የነጻ ጥያቄ ብዛት እና የክፍያ ሁኔታ (Status: 'free', 'pending', 'paid') መከታተያ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            free_questions_used INTEGER DEFAULT 0,
            payment_status TEXT DEFAULT 'free'
        )
    """)

    conn.commit()
    conn.close()


# /start ትዕዛዝ - ዋናው ማስተካከያ ሜኑ
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # ተጠቃሚው በዳታቤዝ ውስጥ መኖሩን ማረጋገጥ
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, free_questions_used, payment_status) VALUES (?, 0, 'free')",
                   (user_id,))
    conn.commit()
    conn.close()

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💻 Computer Science", callback_data="dept_cs"),
        types.InlineKeyboardButton(text="📡 Other Tech Dept", callback_data="dept_other")
    )
    builder.row(
        types.InlineKeyboardButton(text="📊 My Progress", callback_data="my_progress"),
        types.InlineKeyboardButton(text="🔖 Bookmarks", callback_data="my_bookmarks")
    )
    builder.row(
        types.InlineKeyboardButton(text="🎓 Tutorial Package (Upgrade)", callback_data="tutorial_package")
    )
    builder.row(
        types.InlineKeyboardButton(text="🎲 Random Quiz", callback_data="random_quiz"),
        types.InlineKeyboardButton(text="ℹ️ Help", callback_data="help_menu")
    )

    welcome_text = (
        f"👋 **ሰላም {user_name}!**\n\n"
        f"🎓 **ወደ WanK Exit Exam ዝግጅት ቦት እንኳን ደህና መጡ።**\n"
        f"ለኮምፒውተር ሳይንስ እና ለሌሎች ዲፓርትመንቶች ጥያቄዎች እና ማብራሪያዎች እዚህ ያገኛሉ።\n\n"
        f"👇 ከታች ከሚገኙት አማራጮች ውስጥ የሚፈልጉትን ይምረጡ:"
    )

    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 1. Computer Science አማራጭ ሲነካ (2018 ጥር ፈተና)
@dp.callback_query(F.data == "dept_cs")
async def start_cs_exam(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT free_questions_used, payment_status FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    free_used = user_data[0] if user_data else 0
    pay_status = user_data[1] if user_data else 'free'

    # ክፍያ ካልፈጸመ እና 3ቱ ነጻ ጥያቄዎች ካለቁ ክፍያ ይጠይቅ
    if pay_status != 'paid' and free_used >= 3:
        await send_payment_prompt(callback.message)
        return

    # የመጀመሪያውን ጥያቄ ማምጣት
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d FROM questions WHERE exam_year = '2018 ጥር' LIMIT 1")
    q = cursor.fetchone()
    conn.close()

    if q:
        q_id, q_text, opt_a, opt_b, opt_c, opt_d = q

        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text=f"A) {opt_a}", callback_data=f"ans_{q_id}_A"))
        builder.row(types.InlineKeyboardButton(text=f"B) {opt_b}", callback_data=f"ans_{q_id}_B"))
        builder.row(types.InlineKeyboardButton(text=f"C) {opt_c}", callback_data=f"ans_{q_id}_C"))
        builder.row(types.InlineKeyboardButton(text=f"D) {opt_d}", callback_data=f"ans_{q_id}_D"))

        rem_text = f" (ቀሪ ነጻ ጥያቄ: {3 - free_used})" if pay_status != 'paid' else " (VIP የተከፈተ 🌟)"
        await callback.message.answer(f"📝 **Computer Science Exit Exam - Q1{rem_text}:**\n\n{q_text}",
                                      reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await callback.message.answer("⚠️ በዳታቤዙ ውስጥ የኮምፒውተር ሳይንስ ጥያቄዎች አልተገኙም!")


# 2. የክፍያ ጥያቄ ማሳያ (50 Birr እና የክፍያ አማራጮች)
async def send_payment_prompt(message: types.Message):
    pay_text = (
        f"🔒 **የነጻ ጥያቄ ገደብዎ አልቋል!**\n\n"
        f"💰 **ክፍያው 50 Birr ብቻ ነው!**\n"
        f"ይህን ከከፈሉ ሙሉውን ጥያቄ እና ማብራሪያ ማግኘት ይችላሉ። እባክዎ ከታች ባሉት የክፍያ አማራጮች ክፍያ ይፈጽሙ፡\n\n"
        f"📱 **Telebirr:** `0919245693` (Negash Wonde)\n"
        f"🏦 **CBE (Commercial Bank of Ethiopia):** `100268717823` (Negash Wonde)\n\n"
        f"📸 ክፍያ ከፈጸሙ በኋላ **የክፍያ ማረጋገጫ (Screenshot)** ፎቶ ወደዚህ ቦት ይላኩ! አድሚኑ ወዲያውኑ አረጋግጦ ይከፍትልዎታል።"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📤 Screenshot ልክ (Admin እዲያይ)", callback_data="upload_screenshot_info"))
    await message.answer(pay_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data == "upload_screenshot_info")
async def screenshot_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📸 እባክዎ የክፍያ ማረጋገጫ (Screenshot) ምስል በቀጥታ በዚህ ቻት ውስጥ ፎቶውን ይላኩ። አድሚኑ ወዲያውኑ አረጋግጦ ይከፍትልዎታል!")


# 3. ተማሪዎች የሚልኩትን የክፍያ ስክሪንሾት (ፎቶ) መቀበል እና ወደ አድሚን ማስተላለፍ
@dp.message(F.photo)
async def handle_payment_screenshot(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    photo_id = message.photo[-1].file_id

    # ለተማሪው ማሳወቂያ መስጠት
    await message.answer("📥 **የክፍያ ስክሪንሾትዎ ደርሷል!** አድሚኑ (Negash) እስኪያረጋግጠው በጥቂት ደቂቃዎች ውስጥ ይጠብቁ።")

    # አድሚኑን ማሳወቅ እና Approve/Reject ቁልፎችን ማሳየት
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ Approve (አጽድቅ)", callback_data=f"app_{user_id}"),
        types.InlineKeyboardButton(text="❌ Reject (ውድቅ አድርግ)", callback_data=f"rej_{user_id}")
    )

    admin_caption = (
        f"🔔 **አዲስ የክፍያ ማረጋገጫ (Screenshot) መጥቷል!**\n\n"
        f"👤 ስም: {user_name}\n"
        f"🔗 ዩዘርናም: @{username if username else 'N/A'}\n"
        f"🆔 User ID: `{user_id}`"
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=admin_caption,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# 4. አድሚኑ Approve ሲያደርግ
@dp.callback_query(F.data.startswith("app_"))
async def admin_approve(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ ይህንን እርምጃ መውሰድ የሚችለው አድሚኑ ብቻ ነው!", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[1])

    # በዳታቤዝ ውስጥ payment_status ወደ 'paid' መቀየር
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET payment_status = 'paid' WHERE user_id = ?", (target_user_id,))
    conn.commit()
    conn.close()

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **[STATUS: APPROVED ✅]**",
                                        reply_markup=None)
    await callback.answer("ክፍያው ጽድቋል!")

    # ለተማሪው መልእክት መላክ
    try:
        await bot.send_message(
            target_user_id,
            "🎉 **እንኳን ደስ አለዎት!** አድሚኑ ክፍያዎን አረጋግጦታል (Approved)። አሁን ሙሉውን የ 2018 Exit Exam ጥያቄዎች እና ማብራሪያዎች ያለ ገደብ መሥራት ይችላሉ! 🚀",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending message to user: {e}")


# 5. አድሚኑ Reject ሲያደርግ
@dp.callback_query(F.data.startswith("rej_"))
async def admin_reject(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ ይህንን እርምጃ መውሰድ የሚችለው አድሚኑ ብቻ ነው!", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[1])

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **[STATUS: REJECTED ❌]**",
                                        reply_markup=None)
    await callback.answer("ክፍያው ውድቅ ተደርጓል!")

    # ለተማሪው መልእክት መላክ
    try:
        await bot.send_message(
            target_user_id,
            "❌ **ክፍያዎ ውድቅ ተደርጓል (Rejected)።** እባክዎ ትክክለኛውን የክፍያ ስክሪንሾት (Screenshot) በድጋሚ ይላኩ ወይም በ 0919245693 ይደውሉልን።",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending message to user: {e}")


# 6. መልስ ማረጋገጫ እና Next ቁልፍ ማሳያ
@dp.callback_query(F.data.startswith("ans_"))
async def check_answer(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    parts = callback.data.split("_")
    q_id = parts[1]
    chosen_opt = parts[2]

    # የተጠቃሚውን ነጻ ጥያቄ ብዛት በአንድ መጨመር
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT free_questions_used, payment_status FROM users WHERE user_id = ?", (user_id,))
    res_user = cursor.fetchone()

    if res_user:
        free_used, pay_status = res_user
        if pay_status != 'paid':
            cursor.execute("UPDATE users SET free_questions_used = free_questions_used + 1 WHERE user_id = ?",
                           (user_id,))
            conn.commit()

    # ትክክለኛውን መልስ ከዳታቤዝ ማምጣት
    cursor.execute("SELECT correct_answer, explanation FROM questions WHERE id = ?", (q_id,))
    res = cursor.fetchone()
    conn.close()

    if res:
        correct, explanation = res

        if chosen_opt == correct:
            result_text = "✅ **ትክክል ነው! (Correct)**"
        else:
            result_text = f"❌ **ስህተት ነው። ትክክለኛው መልስ: {correct}**"

        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="➡️ Next Question (ቀጣይ)", callback_data=f"next_{q_id}"))

        feedback = f"{result_text}\n\n💡 **ማብራሪያ (Explanation):**\n{explanation}"
        await callback.message.answer(feedback, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 7. ቀጣይ ጥያቄ (Next Question ሎጂክ)
@dp.callback_query(F.data.startswith("next_"))
async def next_question(callback: types.CallbackQuery):
    await callback.answer()

    current_id = int(callback.data.split("_")[1])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d FROM questions WHERE id > ? AND exam_year = '2018 ጥር' ORDER BY id ASC LIMIT 1",
        (current_id,),
    )
    q = cursor.fetchone()
    conn.close()

    if q:
        q_id, q_text, opt_a, opt_b, opt_c, opt_d = q

        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text=f"A) {opt_a}", callback_data=f"ans_{q_id}_A"))
        builder.row(types.InlineKeyboardButton(text=f"B) {opt_b}", callback_data=f"ans_{q_id}_B"))
        builder.row(types.InlineKeyboardButton(text=f"C) {opt_c}", callback_data=f"ans_{q_id}_C"))
        builder.row(types.InlineKeyboardButton(text=f"D) {opt_d}", callback_data=f"ans_{q_id}_D"))

        await callback.message.answer(
            f"📝 **2018 Exit Exam - Next Question:**\n\n{q_text}",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown",
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
        await callback.message.answer(
            "🎉 **እንኳን ደስ አለዎት!** የ 2018 ጥያቄዎችን በሙሉ አጠናቀዋል።",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )


# 8. Random Quiz (10 ጥያቄዎች በዘፈቀደ)
@dp.callback_query(F.data == "random_quiz")
async def random_quiz_handler(callback: types.CallbackQuery):
    await callback.answer()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d FROM questions ORDER BY RANDOM() LIMIT 1")
    q = cursor.fetchone()
    conn.close()

    if q:
        q_id, q_text, opt_a, opt_b, opt_c, opt_d = q
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text=f"A) {opt_a}", callback_data=f"ans_{q_id}_A"))
        builder.row(types.InlineKeyboardButton(text=f"B) {opt_b}", callback_data=f"ans_{q_id}_B"))
        builder.row(types.InlineKeyboardButton(text=f"C) {opt_c}", callback_data=f"ans_{q_id}_C"))
        builder.row(types.InlineKeyboardButton(text=f"D) {opt_d}", callback_data=f"ans_{q_id}_D"))

        await callback.message.answer(f"🎲 **Random Quiz Question:**\n\n{q_text}", reply_markup=builder.as_markup(),
                                      parse_mode="Markdown")
    else:
        await callback.message.answer("⚠️ በዳታቤዙ ውስጥ ጥያቄዎች አልተገኙም!")


# 9. Tutorial Package (ለኮምፒውተር ሳይንስ 15ቱ ኮርሶች)
@dp.callback_query(F.data == "tutorial_package")
async def tutorial_package_handler(callback: types.CallbackQuery):
    await callback.answer()

    courses_text = (
        "🎓 **Computer Science Tutorial Packages & Core Courses**\n\n"
        "ይህ ፓኬጅ ለኮምፒውተር ሳይንስ (CS) Exit Exam ተማሪዎች በሙሉ ጥልቀት የተዘጋጀ ሲሆን የሚከተሉትን 15 ዋና ዋና ኮርሶች ይሸፍናል፦\n\n"
        "1️⃣ Computer Programming\n"
        "2️⃣ Object-Oriented Programming (OOP)\n"
        "3️⃣ Database Systems\n"
        "4️⃣ Computer Organization and Architecture\n"
        "5️⃣ Data Communication and Computer Networking\n"
        "6️⃣ Data Structures and Algorithms\n"
        "7️⃣ Web Programming\n"
        "8️⃣ Automata and Complexity Theory\n"
        "9️⃣ Operating Systems\n"
        "🔟 Software Engineering\n"
        "1️⃣1️⃣ Design and Analysis of Algorithms\n"
        "1️⃣2️⃣ Introduction to Artificial Intelligence\n"
        "1️⃣3️⃣ Computer Security\n"
        "1️⃣4️⃣ Network and System Administration\n"
        "1️⃣5️⃣ Compiler Design\n\n"
        "💡 **ማስታወሻ:** እነዚህ ኮርሶች ለኮምፒውተር ሳይንስ ኤክዚት ፈተና 100% አጋዥ እና ፕሪሚየም ጥያቄዎችን የያዙ ናቸው!"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 ወደ ዋናው ሜኑ ተመለስ", callback_data="back_menu"))
    await callback.message.answer(courses_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 10. Help ሜኑ
@dp.callback_query(F.data == "help_menu")
async def help_handler(callback: types.CallbackQuery):
    await callback.answer()
    help_text = (
        "ℹ️ **WanK Bot Help & Support Center**\n\n"
        "ማንኛውንም ጥያቄ፣ ሃሳብ ወይም የክፍያ ማረጋገጫ ጉዳይ ካለዎት በቀጥታ በሚከተሉት አድራሻዎች ማግኘት ይችላሉ፦\n\n"
        "📞 **ስልክ ቁጥር:** `0919245693`\n"
        "ቴሌግራም አድራሻ: @neguman19\n\n"
        "💡 **ጠቃሚ ምክር ለተማሪዎች:**\n"
        "• ነጻ ጥያቄዎችዎን በጥንቃቄ ይጠቀሙ።\n"
        "• ክፍያ ሲፈጽሙ የትራንዛክሽን ስክሪንሾት (Screenshot) መላክዎን አይርሱ።\n"
        "• በየቀኑ አዳዲስ የፈተና ጥያቄዎች ይዘመናሉ!"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 ወደ ዋናው ሜኑ ተመለስ", callback_data="back_menu"))
    await callback.message.answer(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# ሌሎች ዲፓርትመንቶች (ለነገ የሚጨመሩ)
@dp.callback_query(F.data == "dept_other")
async def other_dept_handler(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("🚀 ሌሎች ዲፓርትመንቶች በቅርቡ ይጨመራሉ! ጠብቁን።")


@dp.callback_query(F.data == "my_progress")
async def progress_handler(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("📊 የእርስዎ የፈተና ሂደት (Progress) በቅርቡ ይለቀቃል!")


@dp.callback_query(F.data == "my_bookmarks")
async def bookmarks_handler(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("🔖 ያስቀመጧቸው (Bookmarks) ጥያቄዎች እዚህ ይታያሉ።")


@dp.callback_query(F.data == "back_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)


async def main():
    init_db()

    # Flask ሰርቨርን ማስጀመር (Render እንዲሰራ)
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("🌐 Flask Web Server started successfully on port 8080")

    print("🚀 WanK Exam Master Bot is running live!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())