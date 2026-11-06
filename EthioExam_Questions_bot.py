import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import sqlite3
import os
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

# የባነር ፎቶ File ID (እዚህ ጋር የፎቶዎን file_id ወይም ሊንክ ያስገቡ)
WELCOME_BANNER_PHOTO = "YOUR_PHOTO_FILE_ID_OR_URL_HERE"


# ዳታቤዙን እና ሠንጠረዦችን ማቀናጀት
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
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


# ከታች በግራ በኩል የሚታየውን ሶስት ሰረዝ ያለው የ Menu ሰማያዊ ቁልፍ (Reply Keyboard)
def get_main_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="≡ Menu")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


# /start ትዕዛዝ እና የ "≡ Menu" ቴክስት መልእክት መቀበያ
@dp.message(F.text == "≡ Menu")
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, free_questions_used, payment_status, paid_department) VALUES (?, 0, 'free', '')",
        (user_id,))
    conn.commit()
    conn.close()

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💻 Computer Science  >", callback_data="dept_cs_menu"),
        types.InlineKeyboardButton(text="📡 Information Technology  >", callback_data="dept_it_menu")
    )
    builder.row(
        types.InlineKeyboardButton(text="📊 My Progress  >", callback_data="my_progress"),
        types.InlineKeyboardButton(text="🔖 Bookmarks  >", callback_data="my_bookmarks")
    )
    builder.row(
        types.InlineKeyboardButton(text="📄 Documents (PPT/PDF)  >", callback_data="tutorial_package"),
        types.InlineKeyboardButton(text="🎲 Random Quiz  >", callback_data="rand_start_1_0_0")
    )
    builder.row(
        types.InlineKeyboardButton(text="🎧 Help & Support  >", callback_data="help_menu"),
        types.InlineKeyboardButton(text="ℹ️ About Bot  >", callback_data="about_bot")
    )

    welcome_text = (
        f"👋 **ሰላም {user_name}!**\n\n"
        f"🎓 **ወደ WanK Exam ዝግጅት ቦት እንኳን ደህና መጡ።**\n"
        f"ለኮምፒውተር ሳይንስ (CS), ለአይቲ (IT), Freshman and Remedial ጥያቄዎች እና ማብራሪያዎች እዚህ ያገኛሉ።\n\n"
        f"👇 ከታች ከሚገኙት አማራጮች ውስጥ የሚፈልጉትን ይምረጡ:"
    )

    await message.answer("👇", reply_markup=get_main_reply_keyboard())

    try:
        await message.answer_photo(
            photo=WELCOME_BANNER_PHOTO,
            caption=welcome_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception:
        await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 1. Computer Science የዓመታት/ወራት ምርጫ ሜኑ
@dp.callback_query(F.data == "dept_cs_menu")
async def cs_years_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 የጥር ወር ፈተና", callback_data="start_exam_CS_ጥር"),
        types.InlineKeyboardButton(text="📅 የሰኔ ወር ፈተና", callback_data="start_exam_CS_ሰኔ")
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    await callback.message.edit_text(
        "💻 **Computer Science Exit Exam**\n\nእባክዎ መፈተን የሚፈልጉትን የፈተና ጊዜ (ወር) ይምረጡ:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# 2. Information Technology የዓመታት/ወራት ምርጫ ሜኑ
@dp.callback_query(F.data == "dept_it_menu")
async def it_years_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 የጥር ወር ፈተና", callback_data="start_exam_IT_ጥር"),
        types.InlineKeyboardButton(text="📅 የሰኔ ወር ፈተና", callback_data="start_exam_IT_ሰኔ")
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    await callback.message.edit_text(
        "📡 **Information Technology (IT) Exit Exam**\n\nእባክዎ መፈተን የሚፈልጉትን የፈተና ጊዜ (ወር) ይምረጡ:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# 3. ፈተና መጀመሪያ (የተከፈተለትን ቼክ ማድረግ)
@dp.callback_query(F.data.startswith("start_exam_"))
async def start_specific_exam(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    subject_code = parts[2]
    exam_period = parts[3]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT free_questions_used, payment_status, paid_department FROM users WHERE user_id = ?",
                   (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    free_used = user_data[0] if user_data else 0
    pay_status = user_data[1] if user_data else 'free'
    paid_depts = user_data[2] if user_data else ''

    pay_key = f"{subject_code}_{exam_period}"

    # ተጠቃሚው ክፍሉን ከፍቶታል ወይስ አልከፈተም የሚለውን ማረጋገጫ (ብዙ ክፍሎችን መያዝ እንዲችል check ይደረጋል)
    is_paid_for_this = pay_status == 'paid' and pay_key in paid_depts.split(",")

    if not is_paid_for_this and free_used >= 3:
        await send_payment_prompt(callback.message, f"{subject_code} ({exam_period})", pay_key)
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d FROM questions WHERE subject = ? AND exam_year = ? LIMIT 1",
        (subject_code, exam_period)
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
        builder.row(
            types.InlineKeyboardButton(text="🔖 Bookmark", callback_data=f"bm_{q_id}"),
            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu")
        )

        rem_text = f" (ቀሪ ነጻ ጥያቄ: {3 - free_used})" if not is_paid_for_this else " (VIP የተከፈተ 🌟)"
        await callback.message.answer(
            f"📝 **{subject_code} ({exam_period}) Exit Exam - Q1{rem_text}:**\n\n{q_text}",
            reply_markup=builder.as_markup(), parse_mode="Markdown"
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
        await callback.message.answer(f"⚠️ በዳታቤዙ ውስጥ ለ **{subject_code} ({exam_period})** የተመዘገቡ ጥያቄዎች አልተገኙም!",
                                      reply_markup=builder.as_markup())


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


# 5. ተማሪዎች የሚልኩትን የክፍያ ስክሪንሾት መቀበል (ለአድሚኑ Multi-select ማሳየት)
@dp.message(F.photo)
async def handle_payment_screenshot(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    photo_id = message.photo[-1].file_id

    await message.answer("📥 **የክፍያ ስክሪንሾትዎ ደርሷል!** አድሚኑ እስኪያረጋግጠው በጥቂት ደቂቃዎች ውስጥ ይጠብቁ።")

    builder = InlineKeyboardBuilder()
    # አድሚኑ ከሁለት ወይም ከሶስት በላይ በአንድ ጊዜ መርጦ ማጽደቅ እንዲችል
    builder.row(
        types.InlineKeyboardButton(text="☑️ CS - ጥር", callback_data=f"toggle_{user_id}_CS_ጥር"),
        types.InlineKeyboardButton(text="☑️ CS - ሰኔ", callback_data=f"toggle_{user_id}_CS_ሰኔ")
    )
    builder.row(
        types.InlineKeyboardButton(text="☑️ IT - ጥር", callback_data=f"toggle_{user_id}_IT_ጥር"),
        types.InlineKeyboardButton(text="☑️ IT - ሰኔ", callback_data=f"toggle_{user_id}_IT_ሰኔ")
    )
    builder.row(types.InlineKeyboardButton(text="🚀 የተመረጡትን አጽድቅ (Approve)", callback_data=f"finalize_app_{user_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ Reject", callback_data=f"rej_{user_id}"))

    admin_caption = (
        f"🔔 **አዲስ የክፍያ ማረጋገጫ መጥቷል!**\n\n"
        f"👤 ስም: {user_name}\n"
        f"🔗 ዩዘርናም: @{username if username else 'N/A'}\n"
        f"🆔 User ID: `{user_id}`\n\n"
        f"📌 *እባክዎ የሚፈልጉትን ፈተና/ክፍል ከላይ በመንካት (እየመረጡ) ከዛ 'የተመረጡትን አጽድቅ' የሚለውን ይጫኑ።*"
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=admin_caption,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# የትኞቹ ክፍሎች እንደተመረጡ በጊዜያዊነት መያዣ (Dictionary)
admin_selections = {}


@dp.callback_query(F.data.startswith("toggle_"))
async def admin_toggle_selection(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ አድሚኑ ብቻ ነው!", show_alert=True)
        return

    parts = callback.data.split("_")
    target_user_id = int(parts[1])
    dept_code = parts[2]
    period = parts[3]
    key = f"{dept_code}_{period}"

    if target_user_id not in admin_selections:
        admin_selections[target_user_id] = set()

    if key in admin_selections[target_user_id]:
        admin_selections[target_user_id].remove(key)
        await callback.answer(f"❌ {key} ተሰርዟል")
    else:
        admin_selections[target_user_id].add(key)
        await callback.answer(f"✅ {key} ተመርጧል")


# አድሚኑ መርጦ ጨርሶ ሲያጸድቅ (Finalize Approve)
@dp.callback_query(F.data.startswith("finalize_app_"))
async def admin_finalize_approve(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ አድሚኑ ብቻ ነው!", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[2])
    selected_keys = admin_selections.get(target_user_id, set())

    if not selected_keys:
        await callback.answer("⚠️ እባክዎ ቢያንስ አንድ ኮርስ/ወር ይምረጡ!", show_alert=True)
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # የያዛቸውን የቀድሞ የተከፈቱ ክፍሎች ማምጣት
    cursor.execute("SELECT paid_department FROM users WHERE user_id = ?", (target_user_id,))
    res = cursor.fetchone()
    existing_depts = res[0].split(",") if res and res[0] else []

    # አዲሶቹን መደመር (Duplicate እንዳይሆን set መጠቀም)
    combined_depts = set(existing_depts).union(selected_keys)
    new_paid_str = ",".join(filter(None, combined_depts))

    cursor.execute("UPDATE users SET payment_status = 'paid', paid_department = ? WHERE user_id = ?",
                   (new_paid_str, target_user_id))
    conn.commit()
    conn.close()

    # ከዲክሽነሪ ማጽዳት
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
            f"🎉 **እንኳን ደስ አለዎት!** አድሚኑ ክፍያዎን አረጋግጦታል (Approved)። አሁን የተመረጡት ሙሉ ጥያቄዎች ተከፍተውልዎታል! 🚀",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending message to user: {e}")


# 6. አድሚኑ Reject ሲያደርግ
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


# 7. መልስ ማረጋገጫ
@dp.callback_query(F.data.startswith("ans_"))
async def check_answer(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    parts = callback.data.split("_")
    q_id = parts[1]
    chosen_opt = parts[2]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT free_questions_used, payment_status, paid_department FROM users WHERE user_id = ?",
                   (user_id,))
    res_user = cursor.fetchone()

    cursor.execute("SELECT subject, exam_year FROM questions WHERE id = ?", (q_id,))
    q_info = cursor.fetchone()

    pay_key = "CS_ጥር"
    if q_info:
        pay_key = f"{q_info[0]}_{q_info[1]}"

    if res_user:
        free_used, pay_status, paid_depts = res_user
        is_paid = pay_status == 'paid' and pay_key in paid_depts.split(",")
        if not is_paid:
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

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="➡️ Next Question (ቀጣይ)", callback_data=f"next_{q_id}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    feedback = f"{result_text}\n\n💡 **ማብራሪያ (Explanation):**\n{explanation}"
    await callback.message.answer(feedback, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 8. ቀጣይ ጥያቄ
@dp.callback_query(F.data.startswith("next_"))
async def next_question(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    current_id = int(callback.data.split("_")[1])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subject, exam_year FROM questions WHERE id = ?", (current_id,))
    q_info = cursor.fetchone()

    if not q_info:
        conn.close()
        await callback.message.answer("⚠️ ጥያቄው አልተገኘም!", reply_markup=InlineKeyboardBuilder().row(
            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu")).as_markup())
        return

    subj, year = q_info
    pay_key = f"{subj}_{year}"

    cursor.execute("SELECT free_questions_used, payment_status, paid_department FROM users WHERE user_id = ?",
                   (user_id,))
    user_data = cursor.fetchone()

    free_used = user_data[0] if user_data else 0
    pay_status = user_data[1] if user_data else 'free'
    paid_depts = user_data[2] if user_data else ''

    is_paid = pay_status == 'paid' and pay_key in paid_depts.split(",")

    if not is_paid and free_used >= 3:
        conn.close()
        await send_payment_prompt(callback.message, f"{subj} ({year})", pay_key)
        return

    cursor.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d FROM questions WHERE id > ? AND subject = ? AND exam_year = ? ORDER BY id ASC LIMIT 1",
        (current_id, subj, year),
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
        builder.row(
            types.InlineKeyboardButton(text="🔖 Bookmark", callback_data=f"bm_{q_id}"),
            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu")
        )

        rem_text = f" (ቀሪ ነጻ ጥያቄ: {3 - free_used})" if not is_paid else " (VIP የተከፈተ 🌟)"
        await callback.message.answer(
            f"📝 **{subj} ({year}) - Next Question{rem_text}:**\n\n{q_text}",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown",
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
        await callback.message.answer("🎉 **እንኳን ደስ አለዎት!** በዚህ ምድብ ያሉትን ጥያቄዎች በሙሉ አጠናቀዋል።",
                                      reply_markup=builder.as_markup(), parse_mode="Markdown")


# 9. Bookmark
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


# 10. Bookmarks List
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
            builder.row(types.InlineKeyboardButton(text=f"🔍 ጥያቄ #{q_id} ተመልከት", callback_data=f"ans_{q_id}_A"))
    else:
        bm_text = "🔖 እስካሁን ያቀመጡት ጥያቄ የለም።"

    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(bm_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 11. Progress
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


# 12. Random Quiz
@dp.callback_query(F.data.startswith("rand_start_"))
async def random_quiz_start(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split("_")
    q_num = int(parts[2])
    current_score = int(parts[3]) if len(parts) > 3 else 0

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, subject, exam_year, question_text, option_a, option_b, option_c, option_d FROM questions ORDER BY RANDOM() LIMIT 1")
    q = cursor.fetchone()
    conn.close()

    if q:
        q_id, subj, year, q_text, opt_a, opt_b, opt_c, opt_d = q
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text=f"A. {opt_a}", callback_data=f"rand_ans_{q_num}_{q_id}_{current_score}_A"))
        builder.row(types.InlineKeyboardButton(text=f"B. {opt_b}", callback_data=f"rand_ans_{q_num}_{q_id}_{current_score}_B"))
        builder.row(types.InlineKeyboardButton(text=f"C. {opt_c}", callback_data=f"rand_ans_{q_num}_{q_id}_{current_score}_C"))
        builder.row(types.InlineKeyboardButton(text=f"D. {opt_d}", callback_data=f"rand_ans_{q_num}_{q_id}_{current_score}_D"))
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

        header_text = f"🎲 **Random Quiz — {q_num}/10**\nSource: {subj} ({year}) Q{q_id}  Score: {current_score}/{q_num - 1 if q_num > 1 else 0}\n\n"
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
        if q_num < 10:
            builder.row(types.InlineKeyboardButton(text="➡️ Next Question (ቀጣይ)", callback_data=f"rand_start_{q_num + 1}_{current_score}"))
        else:
            builder.row(types.InlineKeyboardButton(text=f"🎉 አጠቃላይ ውጤት: {current_score}/10", callback_data="back_menu"))
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

        feedback = f"{res_txt}\n\n💡 **ማብራሪያ (Explanation):**\n{explanation}"
        await callback.message.answer(feedback, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 13. Tutorial Package
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

    await callback.message.edit_text(
        "🎓 **Documents (PPT/PDF) - Categories**\n\nእባክዎ የሚፈልጉትን የትምህርት ዘርፍ ይምረጡ:",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


@dp.callback_query(F.data == "tut_cs")
async def tut_cs_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back to Categories", callback_data="tutorial_package"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "💻 **Computer Science Documents**\n\n📥 [Download CS PPT/PDF](https://t.me/NegashComputerTips/261)",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


@dp.callback_query(F.data == "tut_it")
async def tut_it_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back to Categories", callback_data="tutorial_package"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📡 **Information Technology Documents**\n\n📥 [Download IT PPT/PDF](https://t.me/NegashComputerTips/263)",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


@dp.callback_query(F.data == "tut_fresh_nat")
async def tut_fresh_nat_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back to Categories", callback_data="tutorial_package"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📚 **Freshman (Natural Science) Documents**\n\n📥 [Download Natural Science Materials](https://t.me/NegashComputerTips/264)",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


@dp.callback_query(F.data == "tut_fresh_soc")
async def tut_fresh_soc_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back to Categories", callback_data="tutorial_package"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📚 **Freshman (Social Science) Documents**\n\n📥 [Download Social Science Materials](https://t.me/NegashComputerTips/265)",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


@dp.callback_query(F.data == "tut_rem_nat")
async def tut_rem_nat_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back to Categories", callback_data="tutorial_package"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📖 **Remedial (Natural Science) Documents**\n\n📥 [Download Remedial Natural Materials](https://t.me/NegashComputerTips/266)",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


@dp.callback_query(F.data == "tut_rem_soc")
async def tut_rem_soc_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back to Categories", callback_data="tutorial_package"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📖 **Remedial (Social Science) Documents**\n\n📥 [Download Remedial Social Materials](https://t.me/NegashComputerTips/266)",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


# 14. Help
@dp.callback_query(F.data == "help_menu")
async def help_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text("ℹ️ **Help & Support**\n📞 Phone: `0919245693`\nTelegram: @neguRoha",
                                     reply_markup=builder.as_markup(), parse_mode="Markdown")


# 15. About Bot
@dp.callback_query(F.data == "about_bot")
async def about_bot_handler(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "🤖 **About WankExamBot**\n\n"
        "🎓 WankExamBot is your smart exam assistant designed to help Computer Science, IT, Freshman, and Remedial students prepare effectively for their exit and placement examinations.\n\n"
        "✨ Features:\n"
        "• Practice real exam questions with instant feedback\n"
        "• Track your progress and save bookmarks\n"
        "• Access comprehensive study documents",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# 16. Back Menu
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