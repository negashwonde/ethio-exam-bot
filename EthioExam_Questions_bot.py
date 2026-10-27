import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Configuration
BOT_TOKEN = "8989053444:AAGi6glRFJ4Besq0yvTEJGm2YakJgYnjKdw"  # እዚህጋ ከ BotFather ያገኙትን ቶክን ያስገቡ
ADMIN_ID = 7806847963 # እዚህጋ የራስዎን የቴሌግራም User ID (ቁጥር ብቻ) ያስገቡ

# States for conversation/actions
WAITING_FOR_RECEIPT = 1


# Initialize Database
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_subscribed INTEGER DEFAULT 0
        )
    ''')
    # Questions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            question TEXT,
            options TEXT,
            answer TEXT,
            explanation TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                   (user.id, user.username, user.full_name))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("📚 ጥያቄዎች ለመስራት", callback_data="courses")],
        [InlineKeyboardButton("💳 ክፍያ ለመፈጸም / አባል ለመሆን", callback_data="pay")],
        [InlineKeyboardButton("ℹ️ መረጃ / እገዛ", callback_data="help")]
    ]
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"ሰላም {user.first_name}! እንኳን ወደ ትምህርታዊ የቴሌግራም ቦት በደህና መጡ።\n\n"
        "እባክዎን ከታች ካሉት አማራጮች አንዱን ይምረጡ፡",
        reply_markup=reply_markup
    )


# Menu Navigation & Actions
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "courses":
        # Check payment status
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT is_subscribed FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()

        if res and res[0] == 1:
            keyboard = [
                [InlineKeyboardButton("💻 CS & IT Exit Exam", callback_data="cat_CS_IT")],
                [InlineKeyboardButton("🌱 Freshman Natural", callback_data="cat_Freshman_Nat")],
                [InlineKeyboardButton("📖 Freshman Social", callback_data="cat_Freshman_Soc")],
                [InlineKeyboardButton("🔄 Remedial Natural", callback_data="cat_Remedial_Nat")],
                [InlineKeyboardButton("📚 Remedial Social", callback_data="cat_Remedial_Soc")]
            ]
            await query.edit_message_text("እባክዎን የሚፈልጉትን የትምህርት ዘርፍ ይምረጡ፡", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [[InlineKeyboardButton("💳 አሁኑኑ ይክፈሉ", callback_data="pay")]]
            await query.edit_message_text(
                "❌ ጥያቄዎችን ለመስራት መጀመሪያ ክፍያ መፈጸም አለብዎት።\n"
                "አባል ለመሆን ከታች ያለውን 'ክፍያ ለመፈጸም' የሚለውን ይጫኑ።",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    elif query.data == "pay":
        await query.edit_message_text(
            "💳 **የክፍያ መመሪያ እና አድራሻ:**\n\n"
            "እባክዎን ከታሉት የክፍያ አማራጮች በአንዱ ክፍያውን ይፈጽሙ፡\n\n"
            "📱 **Telebirr:** `0919245693`\n"
            "👤 **ስም:** Negash Wonde\n\n"
            "🏦 **Commercial Bank of Ethiopia (CBE):** `1000268717823`\n"
            "👤 **ስም:** Negash Wonde\n\n"
            "📌 **ቀጣይ እርምጃ:**\n"
            "ክፍያ ከፈጸሙ በኋላ **የደረሰኙን ፎቶ (Screenshot)** በቀጥታ በዚህ ቦት ላይ ይላኩ። አድሚኑ ደረሰኙን ሲያረጋግጥ አካውንትዎ ይመዝገባል!"
        )

    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ **እገዛ እና መረጃ:**\n\n"
            "ይህ ቦት የኮምፒዩተር ሳይንስ/አይቲ Exit Exam፣ የፍሬሽማን እና ሪሚዲያል ጥያቄዎችን ከነማብራሪያቸው እንዲለማመዱ የተዘጋጀ ነው።\n"
            "ጥያቄዎችን ለመጠቀም የክፍያ ደረሰኝዎን መላክ ይኖርብዎታል።"
        )

    elif query.data.startswith("cat_"):
        category = query.data.replace("cat_", "")
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE category = ?", (category,))
        questions = cursor.fetchall()
        conn.close()

        if not questions:
            await query.edit_message_text("ለዚህ ምድብ እስካሁን ምንም ጥያቄ አልተጫነም። በአጭር ጊዜ ውስጥ ይጫናል።")
            return

        for q in questions:
            opts = q[3].split(",")
            text = f"❓ **ጥያቄ:** {q[2]}\n\n" + "\n".join(opts)
            kb = [[InlineKeyboardButton(f"መልስ {q[4]} ይመልከቱ / ማብራሪያ", callback_data=f"ans_{q[0]}")]]
            await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown",
                                           reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("ans_"):
        q_id = query.data.replace("ans_", "")
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT answer, explanation FROM questions WHERE id = ?", (q_id,))
        q_data = cursor.fetchone()
        conn.close()

        if q_data:
            await query.message.reply_text(f"✅ **ትክክለኛ መልስ:** {q_data[0]}\n\n💡 **ማብራሪያ:**\n{q_data[1]}")

    elif query.data.startswith("approve_"):
        target_user_id = int(query.data.replace("approve_", ""))
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_subscribed = 1 WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()

        await query.edit_message_caption(caption="✅ **ክፍያው ጸድቋል! ተማሪው አክሰስ አግኝቷል።**")
        await context.bot.send_message(chat_id=target_user_id,
                                       text="🎉 **እንኳን ደስ አለዎት!** ክፍያዎ ተረጋግጧል። አሁን ጥያቄዎችን መስራት ይችላሉ። /start በማለት ይጀምሩ።")


# Handle Receipt Photo Upload from Student
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not update.message.photo:
        await update.message.reply_text("❌ እባክዎን የክፍያውን ደረሰኝ ፎቶ (Screenshot) ብቻ ይላኩ።")
        return

    photo = update.message.photo[-1].file_id

    keyboard = [[InlineKeyboardButton("✅ Approve (አጽድቅ)", callback_data=f"approve_{user.id}")]]
    caption = f"📩 **አዲስ የክፍያ ደረሰኝ መጥቷል!**\n\n👤 **ተማሪ:** {user.full_name} (@{user.username})\n🆔 **ID:** `{user.id}`"

    # Send photo to Admin
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption, parse_mode="Markdown",
                                 reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("🙏 ደረሰኝዎ ደርሶናል! አድሚኑ መዝግቦ እስከሚያጸድቅልዎ ድረስ በጥቂት ደቂቃዎች ውስጥ ማሳወቂያ ይደርስዎታል።")


# Main Runner
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()