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

# 1. ዌብ ሰርቨር (Flask) ማዋቀር - Render 24/7 እንዲሠራ
app = Flask("")


@app.route("/")
def home():
    return "🤖 WanK CS & IT Exit Exam Bot is running live and active!"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# 2. የቴሌግራም ቦት ማዋቀር
TOKEN = "9095070080:AAHXsxP4rlAI4poCKkylybtmLwener1G9Lk"
ADMIN_ID = 680798556  # የእርስዎ የአድሚን ቴሌግራም ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_NAME = "brand_new_exam.db"


# 3. ዳታቤዙን ማቀናጀት እና የ 2017 እና 2018 ፋይሎችን በራስ-ሰር መጫን
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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

    # የተማሪዎች ሠንጠረዥ (department መረጃን ጨምሮ)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            department TEXT DEFAULT 'CS',
            free_questions_used INTEGER DEFAULT 0,
            payment_status TEXT DEFAULT 'free',
            paid_department TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            user_id INTEGER,
            question_id INTEGER,
            PRIMARY KEY(user_id, question_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER PRIMARY KEY,
            total_attempted INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

    load_all_exam_datasets()


def load_all_exam_datasets():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions")
    conn.commit()
    conn.close()

    print("📂 የ 2017 እና 2018 ዓ.ም የጥር እና ሰኔ ጥያቄዎችን በንጹህ ኢንኮዲንግ መጫን ጀመረ...")

    conn = sqlite3.connect(DB_NAME)

    files_to_import = [
        ("CS_2017_Tir_100_Unique_Final.csv", "CS", "2017_ጥር"),
        ("CS_2017_Sane_100_Unique_Final.csv", "CS", "2017_ሰኔ"),
        ("IT_2017_Tir_100_Unique_Final.csv", "IT", "2017_ጥር"),
        ("IT_2017_Sane_100_Unique_Final.csv", "IT", "2017_ሰኔ"),
        ("CS_2018_Tir_100_Questions_Distinct.csv", "CS", "2018_ጥር"),
        ("CS_2018_Sane_100_Questions_Distinct.csv", "CS", "2018_ሰኔ"),
        ("IT_2018_Tir_100_Questions_Distinct.csv", "IT", "2018_ጥር"),
        ("IT_2018_Sane_100_Questions_Distinct.csv", "IT", "2018_ሰኔ")
    ]

    for file_name, subj, year in files_to_import:
        if os.path.exists(file_name):
            try:
                try:
                    df = pd.read_csv(file_name, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_name, encoding='latin1')

                df['subject'] = subj
                df['exam_year'] = year
                df.to_sql("questions", conn, if_exists="append", index=False)
                print(f"✅ {file_name} (Subject: {subj}, Year: {year}) በትክክል ተጫኗል!")
            except Exception as e:
                print(f"❌ ስህተት በ {file_name} ላይ: {e}")
        else:
            print(f"⚠️ ማስጠንቀቂያ: {file_name} ፎልደሩ ውስጥ አልተገኘም!")

    conn.commit()
    conn.close()
    print("🎉 ሁሉም የ 2017 እና 2018 የጥር እና ሰኔ ጥያቄዎች ተጭነዋል!")


# /start ትዕዛዝ - ተማሪው ዲፓርትመንት እንዲመርጥ ማድረግ
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT department FROM users WHERE user_id = ?", (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        cursor.execute(
            "INSERT INTO users (user_id, department, free_questions_used, payment_status, paid_department) VALUES (?, 'CS', 0, 'free', '')",
            (user_id,))
        conn.commit()
    conn.close()

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💻 Computer Science >", callback_data="dept_cs_menu"),
        types.InlineKeyboardButton(text="📚 Information Technology >", callback_data="dept_it_menu")
    )
    builder.row(
        types.InlineKeyboardButton(text="📊 My Progress >", callback_data="my_progress"),
        types.InlineKeyboardButton(text="🔖 Bookmarks >", callback_data="my_bookmarks")
    )
    builder.row(
        types.InlineKeyboardButton(text="📄 Documents (PP, PDF) >", callback_data="tutorial_package"),
        types.InlineKeyboardButton(text="📝 Random Quiz (10 Qs) >", callback_data="rand_start_1_0")
    )
    builder.row(
        types.InlineKeyboardButton(text="⚙️ ዲፓርትመንት ቀይር (Change Dept)", callback_data="change_dept_menu"),
        types.InlineKeyboardButton(text="🎧 Help & Support >", callback_data="help_menu")
    )

    welcome_text = (
        f"👋 **ሰላም {user_name}!**\n\n"
        f"🎓 **ወደ Wank Exam ዝግጅት ቦት እንኳን ደህና መጡ።**\n"
        f"ለኮምፒውተር ሳይንስ (CS) እና ለአይቲ (IT) የኤክዚት ፈተና ጥያቄዎች እና ማብራሪያዎች እዚህ ያገኛሉ።\n\n"
        f"💡 *ማሳሰቢያ:* የመጀመሪያዎቹ **3 ጥያቄዎች በነጻ** መፈተን ይችላሉ! ከዛ በኋላ ሙሉ ፈተናውን ለመክፈት ክፍያ ይጠየቃል።\n\n"
        f"👇 ከታች ከሚገኙት አማራጮች ውስጥ የሚፈልጉትን ይምረጡ:"
    )

    await message.answer(
        welcome_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# ዲፓርትመንት መቀየሪያ ሜኑ
@dp.callback_query(F.data == "change_dept_menu")
async def change_dept_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💻 Computer Science (CS)", callback_data="set_dept_CS"),
        types.InlineKeyboardButton(text="📡 Information Technology (IT)", callback_data="set_dept_IT")
    )
    builder.row(
        types.InlineKeyboardButton(text="📚 Freshman", callback_data="set_dept_Freshman"),
        types.InlineKeyboardButton(text="📖 Remedial", callback_data="set_dept_Remedial")
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text("🎯 **እባክዎ ትክክለኛ ዲፓርትመንትዎን ይምረጡ:**", reply_markup=builder.as_markup(),
                                     parse_mode="Markdown")


@dp.callback_query(F.data.startswith("set_dept_"))
async def set_department_action(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    selected_dept = callback.data.split("_")[2]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET department = ? WHERE user_id = ?", (selected_dept, user_id))
    conn.commit()
    conn.close()

    await callback.answer(f"✅ ዲፓርትመንትዎ ወደ {selected_dept} ተቀይሯል!", show_alert=True)
    await back_to_menu(callback)


# 1. Computer Science ወራትን መምረጫ ሜኑ
@dp.callback_query(F.data == "dept_cs_menu")
async def cs_years_menu(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    # የፈተና ገደብ ቼክ (አድሚን ካልሆነ በስተቀር ተማሪው የራሱን ዲፓርትመንት ብቻ እንዲፈትን)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT department FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()

    user_dept = res[0] if res else "CS"
    if user_id != ADMIN_ID and user_dept != "CS":
        await callback.answer(
            f"⚠️ ማስጠንቀቂያ፡ የእርስዎ የተመዘገበበት ዲፓርትመንት '{user_dept}' ስለሆነ የ CS ፈተና መፈተን አይችሉም! (ከፈለጉ ሜኑ ላይ በመሄድ ዲፓርትመንትዎን ይቀይሩ)",
            show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 2017 ዓ.ም — ጥር", callback_data="start_exam_CS_2017_ጥር_0_0"),
        types.InlineKeyboardButton(text="📅 2017 ዓ.ም — ሰኔ", callback_data="start_exam_CS_2017_ሰኔ_0_0")
    )
    builder.row(
        types.InlineKeyboardButton(text="📅 2018 ዓ.ም — ጥር", callback_data="start_exam_CS_2018_ጥር_0_0"),
        types.InlineKeyboardButton(text="📅 2018 ዓ.ም — ሰኔ", callback_data="start_exam_CS_2018_ሰኔ_0_0")
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    text_msg = "💻 **Computer Science Exit Exam**\n\nእባክዎ መፈተን የሚፈልጉትን ዓመት እና ወር ይምረጡ:"
    await callback.message.edit_text(text_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 2. Information Technology ወራትን መምረጫ ሜኑ
@dp.callback_query(F.data == "dept_it_menu")
async def it_years_menu(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT department FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()

    user_dept = res[0] if res else "IT"
    if user_id != ADMIN_ID and user_dept != "IT":
        await callback.answer(f"⚠️ ማስጠንቀቂያ፡ የእርስዎ የተመዘገበበት ዲፓርትመንት '{user_dept}' ስለሆነ የ IT ፈተና መፈተን አይችሉም!",
                              show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 2017 ዓ.ም — ጥር", callback_data="start_exam_IT_2017_ጥር_0_0"),
        types.InlineKeyboardButton(text="📅 2017 ዓ.ም — ሰኔ", callback_data="start_exam_IT_2017_ሰኔ_0_0")
    )
    builder.row(
        types.InlineKeyboardButton(text="📅 2018 ዓ.ም — ጥር", callback_data="start_exam_IT_2018_ጥር_0_0"),
        types.InlineKeyboardButton(text="📅 2018 ዓ.ም — ሰኔ", callback_data="start_exam_IT_2018_ሰኔ_0_0")
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    text_msg = "📡 **Information Technology (IT) Exit Exam**\n\nእባክዎ መፈተን የሚፈልጉትን ዓመት እና ወር ይምረጡ:"
    await callback.message.edit_text(text_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 3. ፈተና መጀመሪያ
@dp.callback_query(F.data.startswith("start_exam_"))
async def start_specific_exam(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    subject_code = parts[2]
    year_val = parts[3]
    month_val = parts[4]
    offset_val = int(parts[5]) if len(parts) > 5 else 0
    current_score = int(parts[6]) if len(parts) > 6 else 0

    full_exam_year = f"{year_val}_{month_val}"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT department, free_questions_used, payment_status, paid_department FROM users WHERE user_id = ?",
        (user_id,))
    user_data = cursor.fetchone()

    user_dept = user_data[0] if user_data else "CS"
    free_used = user_data[1] if user_data else 0
    pay_status = user_data[2] if user_data else 'free'
    paid_depts = user_data[3] if user_data else ''

    # ተማሪው የሌላ ዲፓርትመንት ፈተና ለመክፈት ሲሞክር (አድሚን ካልሆነ)
    if user_id != ADMIN_ID and user_dept != subject_code:
        conn.close()
        await callback.message.answer(
            f"⚠️ ይቅርታ! እርስዎ የተመዘገቡት በ **{user_dept}** ዲፓርትመንት ስለሆነ የ **{subject_code}** ፈተና መፈተን አይችሉም።")
        return

    pay_key = f"{subject_code}_{full_exam_year}"
    is_paid_for_this = pay_status == 'paid' and pay_key in paid_depts.split(",")

    if not is_paid_for_this and free_used >= 3 and offset_val >= 3:
        conn.close()
        await send_payment_prompt(callback.message, f"{subject_code} ({year_val} {month_val})", pay_key)
        return

    cursor.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d FROM questions WHERE subject = ? AND exam_year = ? ORDER BY id ASC LIMIT 1 OFFSET ?",
        (subject_code, full_exam_year, offset_val)
    )
    q = cursor.fetchone()
    conn.close()

    if q:
        q_id, q_text, opt_a, opt_b, opt_c, opt_d = q

        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text=f"A) {opt_a}",
                                               callback_data=f"ans_{subject_code}_{year_val}_{month_val}_{offset_val}_{q_id}_{current_score}_A"))
        builder.row(types.InlineKeyboardButton(text=f"B) {opt_b}",
                                               callback_data=f"ans_{subject_code}_{year_val}_{month_val}_{offset_val}_{q_id}_{current_score}_B"))
        builder.row(types.InlineKeyboardButton(text=f"C) {opt_c}",
                                               callback_data=f"ans_{subject_code}_{year_val}_{month_val}_{offset_val}_{q_id}_{current_score}_C"))
        builder.row(types.InlineKeyboardButton(text=f"D) {opt_d}",
                                               callback_data=f"ans_{subject_code}_{year_val}_{month_val}_{offset_val}_{q_id}_{current_score}_D"))
        builder.row(
            types.InlineKeyboardButton(text="🔖 Bookmark", callback_data=f"bm_{q_id}"),
            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu")
        )

        q_num_display = offset_val + 1
        rem_text = f" (ቀሪ ነጻ ጥያቄ: {3 - free_used})" if not is_paid_for_this else " (VIP የተከፈተ 🌟)"
        score_display = f" | Score: {current_score}/{offset_val}" if offset_val > 0 else ""

        await callback.message.answer(
            f"📝 **{subject_code} ({year_val} {month_val}) Exit Exam — Q{q_num_display}{score_display}{rem_text}:**\n\n{q_text}",
            reply_markup=builder.as_markup(), parse_mode="Markdown"
        )
    else:
        percentage = int((current_score / offset_val) * 100) if offset_val > 0 else 0
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

        summary_text = (
            f"🎉 **እንኳን ደስ አለዎት!** በዚህ ምድብ ያሉትን ጥያቄዎች በሙሉ አጠናቀዋል።\n\n"
            f"📊 **የእርስዎ ውጤት (Final Score):**\n"
            f"✅ ትክክለኛ መልሶች: **{current_score}/{offset_val}**\n"
            f"💯 መቶኛ ውጤት: **{percentage}%**"
        )
        await callback.message.answer(summary_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 4. የክፍያ ጥያቄ ማሳያ
async def send_payment_prompt(message: types.Message, dept_name: str, pay_key: str):
    pay_text = (
        f"🔒 **3ቱን ነጻ ጥያቄዎች ጨርሰዋል!**\n\n"
        f"🎓 ለ **{dept_name}** ሙሉ ጥያቄዎች እና ማብራሪያዎች ክፍያ መፈጸም አለብዎት።\n"
        f"💰 **ክፍያው 50 Birr ብቻ ነው!**\n\n"
        f"እባክዎ ከታች ባሉት ኦፊሴላዊ የክፍያ አማራጮች ክፍያ ይፈጽሙ፡\n\n"
        f"🏦 **CBE (Commercial Bank of Ethiopia):** `1000268717823` (Negash Wonde)\n"
        f"📱 **Telebirr:** `0919245693` (Negash Wonde)\n\n"
        f"📸 ክፍያ ከፈጸሙ በኋላ **የክፍያ ማረጋገጫ (Screenshot)** ፎቶ ወደዚህ ቦት ይላኩ!"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📤 Screenshot ልክ (Admin እንዲያይ)",
                                           callback_data=f"upload_screenshot_info_{pay_key}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await message.answer(pay_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("upload_screenshot_info_"))
async def screenshot_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📸 እባክዎ የክፍያ ማረጋገጫ (Screenshot) ምስል በቀጥታ በዚህ ቻት ውስጥ ፎቶውን ይላኩ። አድሚኑ ወዲያውኑ አረጋግጦ ይከፍትልዎታል!")


# 5. ተማሪው ስክሪንሾት ሲልክ የዲፓርትመንት መረጃው ለአድሚን በግልጽ እንዲታይ ማድረግ
@dp.message(F.photo)
async def handle_payment_screenshot(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    photo_id = message.photo[-1].file_id

    # የተማሪውን ዲፓርትመንት ከዳታቤዝ እናምጣ
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT department FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()

    student_dept = res[0] if res else "Unknown"

    await message.answer("📥 **የክፍያ ስክሪንሾትዎ ደርሷል!** አድሚኑ እስኪያረጋግጠው በጥቂት ደቂቃዎች ውስጥ ይጠብቁ።")

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="☑️ CS - 2017 ጥር", callback_data=f"toggle_{user_id}_CS_2017_ጥር"),
        types.InlineKeyboardButton(text="☑️ CS - 2017 ሰኔ", callback_data=f"toggle_{user_id}_CS_2017_ሰኔ")
    )
    builder.row(
        types.InlineKeyboardButton(text="☑️ CS - 2018 ጥር", callback_data=f"toggle_{user_id}_CS_2018_ጥር"),
        types.InlineKeyboardButton(text="☑️ CS - 2018 ሰኔ", callback_data=f"toggle_{user_id}_CS_2018_ሰኔ")
    )
    builder.row(
        types.InlineKeyboardButton(text="☑️ IT - 2017 ጥር", callback_data=f"toggle_{user_id}_IT_2017_ጥር"),
        types.InlineKeyboardButton(text="☑️ IT - 2017 ሰኔ", callback_data=f"toggle_{user_id}_IT_2017_ሰኔ")
    )
    builder.row(
        types.InlineKeyboardButton(text="☑️ IT - 2018 ጥር", callback_data=f"toggle_{user_id}_IT_2018_ጥር"),
        types.InlineKeyboardButton(text="☑️ IT - 2018 ሰኔ", callback_data=f"toggle_{user_id}_IT_2018_ሰኔ")
    )
    builder.row(
        types.InlineKeyboardButton(text="📚 Freshman", callback_data=f"toggle_{user_id}_Freshman_All"),
        types.InlineKeyboardButton(text="📖 Remedial", callback_data=f"toggle_{user_id}_Remedial_All")
    )
    builder.row(types.InlineKeyboardButton(text="🚀 የተመረጡትን አጽድቅ (Approve)", callback_data=f"finalize_app_{user_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Reject", callback_data=f"rej_{user_id}"))

    admin_caption = (
        f"🔔 **አዲስ የክፍያ ማረጋገጫ መጥቷል!**\n\n"
        f"👤 የተማሪ ስም: {user_name}\n"
        f"🎯 **የተማሪው ዲፓርትመንት: {student_dept}** 📌 (እባክዎ ይህንን በማየት ትክክለኛውን ፈተና ያጽድቁ!)\n"
        f"🔗 ዩዘርናም: @{username if username else 'N/A'}\n"
        f"🆔 User ID: `{user_id}`\n\n"
        f"📌 *የሚከፈተውን ፈተና ከላይ በመንካት ከዛ 'የተመረጡትን አጽድቅ' የሚለውን ይጫኑ።*"
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=admin_caption,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


admin_selections = {}


@dp.callback_query(F.data.startswith("toggle_"))
async def admin_toggle_selection(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ አድሚኑ ብቻ ነው!", show_alert=True)
        return

    parts = callback.data.split("_")
    target_user_id = int(parts[1])
    dept_code = parts[2]
    year_val = parts[3] if len(parts) > 3 else ""
    period = parts[4] if len(parts) > 4 else ""

    key = f"{dept_code}_{year_val}_{period}" if period else f"{dept_code}"

    if target_user_id not in admin_selections:
        admin_selections[target_user_id] = set()

    if key in admin_selections[target_user_id]:
        admin_selections[target_user_id].remove(key)
        await callback.answer(f"❌ {key} ተሰርዟል")
    else:
        admin_selections[target_user_id].add(key)
        await callback.answer(f"✅ {key} ተመርጧል")


@dp.callback_query(F.data.startswith("finalize_app_"))
async def admin_finalize_approve(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ አድሚኑ ብቻ ነው!", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[2])
    selected_keys = admin_selections.get(target_user_id, set())

    if not selected_keys:
        await callback.answer("⚠️ እባክዎ ቢያንስ አንድ ዲፓርትመንት ወይም ኮርስ ይምረጡ!", show_alert=True)
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT paid_department FROM users WHERE user_id = ?", (target_user_id,))
    res = cursor.fetchone()
    existing_depts = res[0].split(",") if res and res[0] else []

    combined_depts = set(existing_depts).union(selected_keys)
    new_paid_str = ",".join(filter(None, combined_depts))

    cursor.execute("UPDATE users SET payment_status = 'paid', paid_department = ? WHERE user_id = ?",
                   (new_paid_str, target_user_id))
    conn.commit()
    conn.close()

    if target_user_id in admin_selections:
        del admin_selections[target_user_id]

    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ **[APPROVED: {', '.join(selected_keys)} ✅]**",
        reply_markup=None
    )
    await callback.answer("ክፍያው በተሳካ ሁኔታ ጸድቋል!")

    try:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
        await bot.send_message(
            target_user_id,
            f"🎉 **እንኳን ደስ አለዎት!** አድሚኑ ክፍያዎን አረጋግጦታል (Approved)። አሁን የተመረጡት ዲፓርትመንቶች ተከፍተውልዎታል! 🚀",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending message to user: {e}")


@dp.callback_query(F.data.startswith("rej_"))
async def admin_reject(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ አድሚኑ ብቻ ነው!", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[1])
    if target_user_id in admin_selections:
        del admin_selections[target_user_id]

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **[REJECTED ❌]**", reply_markup=None)
    await callback.answer("ውድቅ ተደርጓል!")

    try:
        await bot.send_message(target_user_id, "❌ **ክፍያዎ ውድቅ ተደርጓል (Rejected)።** እባክዎ በትክክል እንደገና ይላኩ።",
                               parse_mode="Markdown")
    except Exception as e:
        print(f"Error: {e}")


# 6. መልስ ማረጋገጫ እና Score ማስቀጠያ ሎጂክ
@dp.callback_query(F.data.startswith("ans_"))
async def check_answer(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    parts = callback.data.split("_")
    subject_code = parts[1]
    year_val = parts[2]
    month_val = parts[3]
    offset_val = int(parts[4])
    q_id = int(parts[5])
    current_score = int(parts[6])
    chosen_opt = parts[7]

    full_exam_year = f"{year_val}_{month_val}"
    pay_key = f"{subject_code}_{full_exam_year}"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT free_questions_used, payment_status, paid_department FROM users WHERE user_id = ?",
                   (user_id,))
    res_user = cursor.fetchone()

    if res_user:
        free_used, pay_status, paid_depts = res_user
        is_paid = pay_status == 'paid' and pay_key in paid_depts.split(",")
        if not is_paid and offset_val < 3:
            cursor.execute("UPDATE users SET free_questions_used = free_questions_used + 1 WHERE user_id = ?",
                           (user_id,))
            conn.commit()

    cursor.execute(
        "INSERT OR IGNORE INTO user_progress (user_id, total_attempted, correct_count, wrong_count) VALUES (?, 0, 0, 0)",
        (user_id,))
    cursor.execute("SELECT correct_answer, explanation FROM questions WHERE id = ?", (q_id,))
    res = cursor.fetchone()

    if res:
        correct, explanation = res
        if chosen_opt == correct:
            current_score += 1
            result_text = "✅ **ትክክል ነው! (Correct)**"
            cursor.execute(
                "UPDATE user_progress SET total_attempted = total_attempted + 1, correct_count = correct_count + 1 WHERE user_id = ?",
                (user_id,))
        else:
            result_text = f"❌ **ስህተት ነው። ትክክለኛው መልስ: {correct}**"
            cursor.execute(
                "UPDATE user_progress SET total_attempted = total_attempted + 1, wrong_count = wrong_count + 1 WHERE user_id = ?",
                (user_id,))
        conn.commit()

    conn.close()

    next_offset = offset_val + 1
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="➡️ Next Question (ቀጣይ)",
                                           callback_data=f"start_exam_{subject_code}_{year_val}_{month_val}_{next_offset}_{current_score}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    feedback = f"{result_text}\n\n💡 **ማብራሪያ (Explanation):**\n{explanation}"
    await callback.message.answer(feedback, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 7. Bookmark
@dp.callback_query(F.data.startswith("bm_"))
async def bookmark_question(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    q_id = int(callback.data.split("_")[1])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO bookmarks (user_id, question_id) VALUES (?, ?)", (user_id, q_id))
        conn.commit()
        await callback.answer("✅ ወደ Bookmarks ተቀምጧል!", show_alert=True)
    except sqlite3.IntegrityError:
        await callback.answer("ℹ️ ቀደም ሲል ተቀምጧል!", show_alert=True)
    conn.close()


# 8. Bookmarks List
@dp.callback_query(F.data == "my_bookmarks")
async def show_bookmarks(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT q.id, q.subject, q.exam_year, q.question_text 
        FROM questions q 
        JOIN bookmarks b ON q.id = b.question_id 
        WHERE b.user_id = ?
    """, (user_id,))
    bookmarks = cursor.fetchall()
    conn.close()

    builder = InlineKeyboardBuilder()
    if bookmarks:
        bm_text = "🔖 **የአስቀመጧቸው (Bookmarks) ጥያቄዎች ዝርዝር:**\n\n"
        for bm in bookmarks:
            q_id, subj, year, q_text = bm
            bm_text += f"📌 ID: {q_id} | [{subj} - {year}]\n{q_text[:50]}...\n\n"
            builder.row(types.InlineKeyboardButton(text=f"🔍 ጥያቄ #{q_id} ተመልከት",
                                                   callback_data=f"ans_{subj}_{year.split('_')[0]}_{year.split('_')[1]}_0_{q_id}_0_A"))
    else:
        bm_text = "🔖 እስካሁን ያቀመጡት ጥያቄ የለም።"

    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(bm_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 9. Progress
@dp.callback_query(F.data == "my_progress")
async def progress_handler(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT total_attempted, correct_count, wrong_count FROM user_progress WHERE user_id = ?",
                   (user_id,))
    prog = cursor.fetchone()
    conn.close()

    total, correct, wrong = prog if prog else (0, 0, 0)
    progress_text = (
        f"📊 **የእርስዎ የፈተና ሂደት (My Progress):**\n\n"
        f"📝 አጠቃላይ የሞከሩት: **{total}**\n"
        f"✅ ትክክለኛ: **{correct}**\n"
        f"❌ ስህተት: **{wrong}**"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(progress_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 10. Random Quiz (10 ጥያቄዎች በዳታቤዝ ውስጥ ያሉትን በዘፈቀደ የሚያመጣ)
@dp.callback_query(F.data.startswith("rand_start_"))
async def random_quiz_start(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split("_")
    q_num = int(parts[2])
    current_score = int(parts[3]) if len(parts) > 3 else 0

    if q_num > 10:
        percentage = int((current_score / 10) * 100)
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

        if percentage >= 80:
            rating = "🌟 በጣም ድንቅ ውጤት! (Excellent)"
        elif percentage >= 50:
            rating = "👍 ጥሩ ጥረት! (Good Job)"
        else:
            rating = "📚 ተጨማሪ ንባብ ይጠይቃል (Needs More Practice)"

        summary_text = (
            f"🎲 **Random Quiz Complete!**\n\n"
            f"📊 Score: **{current_score}/10 ({percentage}%)**\n\n"
            f"📖 {rating}"
        )
        await callback.message.answer(summary_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, subject, exam_year, question_text, option_a, option_b, option_c, option_d FROM questions ORDER BY RANDOM() LIMIT 1")
    q = cursor.fetchone()
    conn.close()

    if q:
        q_id, subj, year, q_text, opt_a, opt_b, opt_c, opt_d = q
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text=f"A. {opt_a}", callback_data=f"rand_ans_{q_num}_{q_id}_{current_score}_A"))
        builder.row(
            types.InlineKeyboardButton(text=f"B. {opt_b}", callback_data=f"rand_ans_{q_num}_{q_id}_{current_score}_B"))
        builder.row(
            types.InlineKeyboardButton(text=f"C. {opt_c}", callback_data=f"rand_ans_{q_num}_{q_id}_{current_score}_C"))
        builder.row(
            types.InlineKeyboardButton(text=f"D. {opt_d}", callback_data=f"rand_ans_{q_num}_{q_id}_{current_score}_D"))
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

        header_text = f"🎲 **Random Quiz — {q_num}/10**\nSource: {subj} ({year}) | Current Score: {current_score}\n\n"
        await callback.message.answer(header_text + q_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await callback.message.answer("⚠️ በዳታቤዙ ውስጥ ጥያቄዎች አልተገኙም!")


@dp.callback_query(F.data.startswith("rand_ans_"))
async def random_quiz_answer(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split("_")
    q_num = int(parts[2])
    q_id = int(parts[3])
    current_score = int(parts[4])
    chosen_opt = parts[5]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT correct_answer, explanation, subject, exam_year FROM questions WHERE id = ?", (q_id,))
    res = cursor.fetchone()
    conn.close()

    if res:
        correct, explanation, subj, year = res
        if chosen_opt == correct:
            current_score += 1
            res_txt = "✅ **ትክክል ነው! (Correct)**"
        else:
            res_txt = f"❌ **ስህተት ነው። ትክክለኛው መልስ: {correct}**"

        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="➡️ Next Question (ቀጣይ)",
                                               callback_data=f"rand_start_{q_num + 1}_{current_score}"))
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

        feedback = f"{res_txt}\n\n💡 **ማብራሪያ (Explanation):**\n{explanation}"
        await callback.message.answer(feedback, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 11. Tutorial Package
@dp.callback_query(F.data == "tutorial_package")
async def tutorial_package_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💻 Computer Science", callback_data="tut_cs"))
    builder.row(types.InlineKeyboardButton(text="📡 Information Technology", callback_data="tut_it"))
    builder.row(
        types.InlineKeyboardButton(text="📚 Freshman (Natural)", callback_data="tut_fresh_nat"),
        types.InlineKeyboardButton(text="📚 Freshman (Social)", callback_data="tut_fresh_soc")
    )
    builder.row(
        types.InlineKeyboardButton(text="📖 Remedial (Natural)", callback_data="tut_rem_nat"),
        types.InlineKeyboardButton(text="📖 Remedial (Social)", callback_data="tut_rem_soc")
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    text_msg = "🎓 **Documents (PPT/PDF) - Categories**\n\nእባክዎ የሚፈልጉትን የትምህርት ዘርፍ ይምረጡ:"
    await callback.message.edit_text(text_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("tut_"))
async def tutorial_links_handler(callback: types.CallbackQuery):
    await callback.answer()
    data = callback.data
    links = {
        "tut_cs": ("💻 Computer Science Documents", "https://t.me/NegashComputerTips/261"),
        "tut_it": ("📡 Information Technology Documents", "https://t.me/NegashComputerTips/263"),
        "tut_fresh_nat": ("📚 Freshman (Natural Science) Documents", "https://t.me/NegashComputerTips/264"),
        "tut_fresh_soc": ("📚 Freshman (Social Science) Documents", "https://t.me/NegashComputerTips/265"),
        "tut_rem_nat": ("📖 Remedial (Natural Science) Documents", "https://t.me/NegashComputerTips/266"),
        "tut_rem_soc": ("📖 Remedial (Social Science) Documents", "https://t.me/NegashComputerTips/266")
    }
    if data in links:
        title, link = links[data]
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Back to Categories", callback_data="tutorial_package"))
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
        text_msg = f"{title}\n\n📥 [Download Material]({link})"
        await callback.message.edit_text(text_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 12. Help
@dp.callback_query(F.data == "help_menu")
async def help_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    text_msg = "ℹ️ **Help & Support**\n📞 Phone: `0919245693`\nTelegram: @neguRoha"
    await callback.message.edit_text(text_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 13. About Bot
@dp.callback_query(F.data == "about_bot")
async def about_bot_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    about_text = (
        "🤖 **About WankExamBot**\n\n"
        "🎓 WankExamBot is your smart exam assistant designed to help Computer Science, IT, Freshman, and Remedial students prepare effectively for their exit and placement examinations.\n\n"
        "✨ Features:\n"
        "• Practice real exam questions with instant feedback\n"
        "• Track your progress and save bookmarks\n"
        "• Access comprehensive study documents"
    )
    await callback.message.edit_text(about_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 14. Back Menu
@dp.callback_query(F.data == "back_menu")
async def back_to_menu(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await cmd_start(callback.message)


async def main():
    init_db()
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("🌐 Flask Web Server started successfully on port 8080")
    print("🚀 WanK Exam Bot is running live!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())