import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
import os
import pandas as pd
from flask import Flask, render_template_string, request, jsonify
from threading import Thread

# 1. ዌብ ሰርቨር (Flask) ማዋቀር - ለ Mini App API እና Render 24/7 አሰራር
app = Flask("")

DB_NAME = "brand_new_exam.db"

# የተሟላ የ Telegram Mini App (Frontend ከቦቱ ሜኑዎች እና ከላኩልኝ ፎቶ ጋር ተመሳሳይ ዲዛይን ያለው)
MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="am">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wank Exam Bot Portal</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0a192f 0%, #172a45 100%);
            color: #ffffff;
            margin: 0;
            padding: 15px;
            text-align: center;
        }
        h1 { color: #38bdf8; font-size: 22px; margin-bottom: 5px; }
        .card {
            background: rgba(30, 41, 59, 0.85);
            padding: 15px;
            border-radius: 12px;
            margin-top: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            border: 1px solid rgba(56, 189, 248, 0.2);
            text-align: left;
        }
        .btn {
            background: linear-gradient(to right, #1d4ed8, #0284c7);
            color: white;
            border: none;
            padding: 12px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            margin-top: 8px;
            width: 100%;
            text-align: left;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .btn:hover { opacity: 0.9; }
        .opt-btn {
            background-color: #334155;
            color: white;
            border: 1px solid #475569;
            padding: 10px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 8px;
            width: 100%;
            text-align: left;
        }
        .opt-btn:hover { background-color: #475569; }
        .correct { background-color: #16a34a !important; }
        .incorrect { background-color: #dc2626 !important; }
        .hidden { display: none; }
        .info-box { font-size: 14px; color: #93c5fd; margin-bottom: 10px; line-height: 1.4; }
    </style>
</head>
<body>
    <h1>🎓 Wank Exam Portal</h1>
    <p id="user-greeting" style="color: #cbd5e1; font-size: 14px;">ሰላም!</p>

    <!-- Main Menu View (ከፎቶው ጋር ተመሳሳይ የሆኑ አማራጮች) -->
    <div id="menu-view" class="card">
        <div class="info-box">👇 ከታች ከሚገኙት አማራጮች ውስጥ የሚፈልጉትን ይምረጡ:</div>
        <button class="btn" onclick="openCategory('CS', '2017_ጥር')">💻 ኮምፒውተር ሳይንስ (CS - 2017 ጥር)</button>
        <button class="btn" onclick="openCategory('CS', '2018_ጥር')">💻 ኮምፒውተር ሳይንስ (CS - 2018 ጥር)</button>
        <button class="btn" onclick="openCategory('IT', '2017_ጥር')">📚 ኢንፎርሜሽን ቴክኖሎጂ (IT - 2017 ጥር)</button>
        <button class="btn" onclick="openCategory('IT', '2018_ጥር')">📚 ኢንፎርሜሽን ቴክኖሎጂ (IT - 2018 ጥር)</button>
        <button class="btn" onclick="alert('📚 Freshman program exams and materials will be updated soon!')">📚 ፍሬሽማን (Freshman)</button>
        <button class="btn" onclick="alert('📖 Remedial program exams and materials will be updated soon!')">📖 ሬሚዲያል (Remedial)</button>
        <button class="btn" onclick="alert('📊 የርስዎን ውጤት ለማየት ዋናውን የቴሌግራም ቦት ይጠቀሙ።')">📊 የእኔ ውጤት (My Progress)</button>
        <button class="btn" onclick="alert('📄 የሰነዶች ማቴሪያሎች በቦቱ ውስጥ በሚገኘው ሊንክ ማውረድ ይችላሉ።')">📄 ሰነዶች (ማቴሪያሎች)</button>
        <button class="btn" onclick="alert('ℹ️ WankExamBot ለሁሉም የዩኒቨርሲቲ ተማሪዎች የተዘጋጀ የዝግጅት ረዳት ነው።')">ℹ️ ስለ ቦቱ (About Bot)</button>
        <button class="btn" onclick="alert('🎧 እርዳታ ለማግኘት በስልክ ቁጥር 0919245693 ወይም @neguRoha ያግኙን።')">🎧 እርዳታ እና ድጋፍ (Support)</button>
    </div>

    <!-- Exam View -->
    <div id="exam-view" class="card hidden">
        <h3 id="q-title" style="color: #38bdf8;">ጥያቄ</h3>
        <p id="q-text" style="font-size: 15px; line-height: 1.5;"></p>

        <button class="opt-btn" id="btn-a" onclick="submitAnswer('A')"></button>
        <button class="opt-btn" id="btn-b" onclick="submitAnswer('B')"></button>
        <button class="opt-btn" id="btn-c" onclick="submitAnswer('C')"></button>
        <button class="opt-btn" id="btn-d" onclick="submitAnswer('D')"></button>

        <p id="explanation" style="margin-top: 15px; font-size: 14px; color: #38bdf8;"></p>
        <button id="next-btn" class="btn hidden" onclick="loadNextQuestion()" style="text-align: center;">ቀጣይ ጥያቄ ➡️</button>
        <button class="btn" onclick="backToMenu()" style="background: #475569; text-align: center; margin-top: 10px;">🏠 ዋና ማውጫ</button>
    </div>

    <!-- Result View -->
    <div id="result-view" class="card hidden" style="text-align: center;">
        <h2>🎉 እንኳን ደስ አለዎት!</h2>
        <p id="final-score" style="font-size: 18px; margin: 15px 0;"></p>
        <button class="btn" onclick="backToMenu()" style="text-align: center;">🏠 ዋና ማውጫ ተመለስ</button>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();

        const user = tg.initDataUnsafe?.user;
        let userId = user ? user.id : 12345;
        if (user) {
            document.getElementById('user-greeting').innerText = `👋 ሰላም, ${user.first_name}!`;
        }

        let currentSubject = '';
        let currentYear = '';
        let questionsList = [];
        let currentIndex = 0;
        let score = 0;

        function openCategory(subj, year) {
            currentSubject = subj;
            currentYear = year;
            fetch(`/api/questions?subject=${subj}&year=${year}&user_id=${userId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.locked) {
                        alert("🔒 3ቱን ነጻ ጥያቄዎች ጨርሰዋል! ሙሉ ፈተናውን ለመክፈት እባክዎ በቦቱ በኩል ክፍያ ፈጽመው ስክሪንሾት ይላኩ።");
                        return;
                    }
                    questionsList = data.questions;
                    if (questionsList.length === 0) {
                        alert("⚠️ በዚህ ምድብ ጥያቄዎች አልተገኙም!");
                        return;
                    }
                    currentIndex = 0;
                    score = 0;
                    document.getElementById('menu-view').classList.add('hidden');
                    document.getElementById('exam-view').classList.remove('hidden');
                    showQuestion();
                });
        }

        function showQuestion() {
            if (currentIndex >= questionsList.length) {
                document.getElementById('exam-view').classList.add('hidden');
                document.getElementById('result-view').classList.remove('hidden');
                document.getElementById('final-score').innerText = `📊 ትክክለኛ መልሶች: ${score} ከ ${questionsList.length}`;
                return;
            }

            let q = questionsList[currentIndex];
            document.getElementById('q-title').innerText = `📝 ጥያቄ ቁጥር ${currentIndex + 1}`;
            document.getElementById('q-text').innerText = q.question_text;

            document.getElementById('btn-a').innerText = `A) ${q.option_a}`;
            document.getElementById('btn-b').innerText = `B) ${q.option_b}`;
            document.getElementById('btn-c').innerText = `C) ${q.option_c}`;
            document.getElementById('btn-d').innerText = `D) ${q.option_d}`;

            ['a', 'b', 'c', 'd'].forEach(opt => {
                let btn = document.getElementById(`btn-${opt}`);
                btn.disabled = false;
                btn.className = "opt-btn";
            });

            document.getElementById('explanation').innerText = "";
            document.getElementById('next-btn').classList.add('hidden');
        }

        function submitAnswer(selectedOpt) {
            let q = questionsList[currentIndex];
            ['a', 'b', 'c', 'd'].forEach(opt => {
                document.getElementById(`btn-${opt}`).disabled = true;
            });

            fetch('/api/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, question_id: q.id, selected: selectedOpt })
            })
            .then(res => res.json())
            .then(data => {
                if (data.is_correct) {
                    score++;
                    document.getElementById(`btn-${selectedOpt.toLowerCase()}`).classList.add('correct');
                } else {
                    document.getElementById(`btn-${selectedOpt.toLowerCase()}`).classList.add('incorrect');
                    document.getElementById(`btn-${data.correct_answer.toLowerCase()}`).classList.add('correct');
                }
                document.getElementById('explanation').innerText = `💡 ማብራሪያ: ${q.explanation || 'ለዚህ ጥያቄ ማብራሪያ አልተሰጠም።'}`;
                document.getElementById('next-btn').classList.remove('hidden');
            });
        }

        function loadNextQuestion() {
            currentIndex++;
            showQuestion();
        }

        function backToMenu() {
            document.getElementById('exam-view').classList.add('hidden');
            document.getElementById('result-view').classList.add('hidden');
            document.getElementById('menu-view').classList.remove('hidden');
        }
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return "🤖 WanK CS & IT Exit Exam Bot & Mini App API is running live!"


@app.route("/webapp")
def webapp():
    return render_template_string(MINI_APP_HTML)


# የ Mini App API ለጥያቄዎች ማቀበያ
@app.route("/api/questions")
def api_questions():
    subj = request.args.get("subject", "CS")
    year = request.args.get("year", "2017_ጥር")
    user_id = int(request.args.get("user_id", 0))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT free_questions_used, payment_status, paid_department FROM users WHERE user_id = ?",
                   (user_id,))
    user_data = cursor.fetchone()

    free_used = user_data[0] if user_data else 0
    pay_status = user_data[1] if user_data else 'free'
    paid_depts = user_data[2] if user_data else ''
    pay_key = f"{subj}_{year}"
    is_paid = pay_status == 'paid' and pay_key in paid_depts.split(",")

    # ነጻ 3 ጥያቄዎች ካለቁ እና አድሚኑ ካልፈቀደ (ክፍያ ካልጸደቀ)
    if not is_paid and free_used >= 3:
        conn.close()
        return jsonify({"locked": True, "questions": []})

    cursor.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation FROM questions WHERE subject = ? AND exam_year = ?",
        (subj, year))
    rows = cursor.fetchall()
    conn.close()

    questions = []
    for r in rows:
        questions.append({
            "id": r[0], "question_text": r[1], "option_a": r[2], "option_b": r[3],
            "option_c": r[4], "option_d": r[5], "correct_answer": r[6], "explanation": r[7]
        })
    return jsonify({"locked": False, "questions": questions})


# የ Mini App API ለምልስ ማረጋገጫ
@app.route("/api/answer", methods=["POST"])
def api_answer():
    data = request.json
    user_id = data.get("user_id")
    q_id = data.get("question_id")
    selected = data.get("selected")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT correct_answer FROM questions WHERE id = ?", (q_id,))
    res = cursor.fetchone()
    correct_ans = res[0] if res else "A"

    is_correct = (selected == correct_ans)

    # ነጻ ጥያቄዎች ብዛት ማዘመን
    cursor.execute("SELECT free_questions_used FROM users WHERE user_id = ?", (user_id,))
    u_res = cursor.fetchone()
    if u_res and u_res[0] < 3:
        cursor.execute("UPDATE users SET free_questions_used = free_questions_used + 1 WHERE user_id = ?", (user_id,))
        conn.commit()

    conn.close()
    return jsonify({"is_correct": is_correct, "correct_answer": correct_ans})


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# 2. የቴሌግራም ቦት ማዋቀር
TOKEN = "9095070080:AAHXsxP4rlAI4poCKkylybtmLwener1G9Lk"
ADMIN_ID = 680798556  # የእርስዎ የአድሚን ቴሌግራም ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            department TEXT DEFAULT 'CS',
            lang TEXT DEFAULT 'am',
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


# ዋናውን ሜኑ የሚያሳይ ሄፐር ፈንክሽን
async def show_main_menu(message_or_callback, user_id, user_name, edit=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT department, lang FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, department, lang, free_questions_used, payment_status, paid_department) VALUES (?, 'CS', 'am', 0, 'free', '')",
            (user_id,))
        conn.commit()
        user_lang = 'am'
    else:
        user_lang = user_data[1]
    conn.close()

    builder = InlineKeyboardBuilder()

    # --- Telegram Mini App Button ---
    builder.row(
        types.InlineKeyboardButton(
            text="🚀 Open Exam Mini App" if user_lang == 'en' else "🚀 ፈተናውን በ ሚኒ አፕ ክፈት",
            web_app=types.WebAppInfo(url="https://ethio-exam-bot-882d.onrender.com/webapp")
        )
    )

    builder.row(
        types.InlineKeyboardButton(text="💻 Computer Science >" if user_lang == 'en' else "💻 ኮምፒውተር ሳይንስ >",
                                   callback_data="dept_cs_menu"),
        types.InlineKeyboardButton(text="📚 Information Technology >" if user_lang == 'en' else "📚 ኢንፎርሜሽን ቴክኖሎጂ >",
                                   callback_data="dept_it_menu")
    )
    builder.row(
        types.InlineKeyboardButton(text="📚 Freshman >" if user_lang == 'en' else "📚 ፍሬሽማን >",
                                   callback_data="dept_freshman_menu"),
        types.InlineKeyboardButton(text="📖 Remedial >" if user_lang == 'en' else "📖 ሬሚዲያል >",
                                   callback_data="dept_remedial_menu")
    )
    builder.row(
        types.InlineKeyboardButton(text="📊 My Progress >" if user_lang == 'en' else "📊 የእኔ ውጤት >",
                                   callback_data="my_progress"),
        types.InlineKeyboardButton(text="🔖 Bookmarks >" if user_lang == 'en' else "🔖 ያስቀመጧቸው >",
                                   callback_data="my_bookmarks")
    )
    builder.row(
        types.InlineKeyboardButton(text="📄 Documents (PP, PDF) >" if user_lang == 'en' else "📄 ሰነዶች (ማቴሪያሎች) >",
                                   callback_data="tutorial_package")
    )
    builder.row(
        types.InlineKeyboardButton(text="⚙️ Change Department" if user_lang == 'en' else "⚙️ ዲፓርትመንት ቀይር",
                                   callback_data="change_dept_menu")
    )
    builder.row(
        types.InlineKeyboardButton(text="ℹ️ About Bot >" if user_lang == 'en' else "ℹ️ ስለ ቦቱ >",
                                   callback_data="about_bot"),
        types.InlineKeyboardButton(text="🎧 Help & Support >" if user_lang == 'en' else "🎧 እርዳታ እና ድጋፍ >",
                                   callback_data="help_menu")
    )
    builder.row(
        types.InlineKeyboardButton(text="🇪🇹 አማርኛ", callback_data="set_lang_am"),
        types.InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")
    )

    if user_lang == 'am':
        welcome_text = (
            f"👋 **ሰላም {user_name}!**\n\n"
            f"🎓 **ወደ Wank Exam ዝግጅት ቦት እንኳን ደህና መጡ።**\n"
            f"ለኮምፒውተር ሳይንስ (CS) እና ለአይቲ (IT) የኤክዚት ፈተና ጥያቄዎች እና ማብራሪያዎች እዚህ ያገኛሉ።\n\n"
            f"💡 *ማሳሰቢያ:* የመጀመሪያዎቹ **3 ጥያቄዎች በነጻ** መፈተን ይችላሉ! ከዛ በኋላ ሙሉ ፈተናውን ለመክፈት ክፍያ ይጠየቃል።\n\n"
            f"👇 ከታች ከሚገኙት አማራጮች ውስጥ የሚፈልጉትን ይምረጡ:"
        )
    else:
        welcome_text = (
            f"👋 **Hello {user_name}!**\n\n"
            f"🎓 **Welcome to Wank Exam Preparation Bot.**\n"
            f"Find Computer Science (CS) and IT exit exam questions and explanations here.\n\n"
            f"💡 *Note:* The first **3 questions are free**! Afterwards, payment is required to unlock the full exam.\n\n"
            f"👇 Select an option below:"
        )

    if edit:
        await message_or_callback.message.edit_text(welcome_text, reply_markup=builder.as_markup(),
                                                    parse_mode="Markdown")
    else:
        await message_or_callback.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# /start ትዕዛዝ[cite: 8]
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await show_main_menu(message, message.from_user.id, message.from_user.first_name, edit=False)


# ቋንቋ መቀየሪያ ሎጂክ[cite: 8]
@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    new_lang = callback.data.split("_")[2]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (new_lang, user_id))
    conn.commit()
    conn.close()

    await callback.answer(f"Language changed to {'አማርኛ' if new_lang == 'am' else 'English'}!")
    await show_main_menu(callback, user_id, callback.from_user.first_name, edit=True)


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
    await callback.message.edit_text("🎯 **እባክዎ ዲፓርትመንትዎን ይምረጡ / Select your department:**",
                                     reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("set_dept_"))
async def set_department_action(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    selected_dept = callback.data.split("_")[2]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET department = ? WHERE user_id = ?", (selected_dept, user_id))
    conn.commit()
    conn.close()

    await callback.answer(f"✅ Department changed to {selected_dept}!", show_alert=True)
    await back_to_menu(callback)


# 1. Computer Science ወራትን መምረጫ ሜኑ
@dp.callback_query(F.data == "dept_cs_menu")
async def cs_years_menu(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT department FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()

    user_dept = res[0] if res else "CS"
    if user_id != ADMIN_ID and user_dept != "CS":
        await callback.answer(f"⚠️ Warning: Your registered department is '{user_dept}'. You cannot access CS exams!",
                              show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 2017 ዓ.ም — Tir", callback_data="start_exam_CS_2017_ጥር_0_0"),
        types.InlineKeyboardButton(text="📅 2017 ዓ.ም — Sane", callback_data="start_exam_CS_2017_ሰኔ_0_0")
    )
    builder.row(
        types.InlineKeyboardButton(text="📅 2018 ዓ.ም — Tir", callback_data="start_exam_CS_2018_ጥር_0_0"),
        types.InlineKeyboardButton(text="📅 2018 ዓ.ም — Sane", callback_data="start_exam_CS_2018_ሰኔ_0_0")
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    text_msg = "💻 **Computer Science Exit Exam**\n\nSelect exam year and month:"
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
        await callback.answer(f"⚠️ Warning: Your registered department is '{user_dept}'. You cannot access IT exams!",
                              show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 2017 ዓ.ም — Tir", callback_data="start_exam_IT_2017_ጥር_0_0"),
        types.InlineKeyboardButton(text="📅 2017 ዓ.ም — Sane", callback_data="start_exam_IT_2017_ሰኔ_0_0")
    )
    builder.row(
        types.InlineKeyboardButton(text="📅 2018 ዓ.ም — Tir", callback_data="start_exam_IT_2018_ጥር_0_0"),
        types.InlineKeyboardButton(text="📅 2018 ዓ.ም — Sane", callback_data="start_exam_IT_2018_ሰኔ_0_0")
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    text_msg = "📡 **Information Technology (IT) Exit Exam**\n\nSelect exam year and month:"
    await callback.message.edit_text(text_msg, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 3. Freshman & Remedial Menu Handlers
@dp.callback_query(F.data == "dept_freshman_menu")
async def freshman_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text("📚 **Freshman Program**\n\nMaterials and exams will be updated soon!",
                                     reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data == "dept_remedial_menu")
async def remedial_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text("📖 **Remedial Program**\n\nMaterials and exams will be updated soon!",
                                     reply_markup=builder.as_markup(), parse_mode="Markdown")


# 4. ፈተና መጀመሪያ (በቦት ቻት በኩል)[cite: 8]
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
        "SELECT department, lang, free_questions_used, payment_status, paid_department FROM users WHERE user_id = ?",
        (user_id,))
    user_data = cursor.fetchone()

    user_dept = user_data[0] if user_data else "CS"
    user_lang = user_data[1] if user_data else "am"
    free_used = user_data[2] if user_data else 0
    pay_status = user_data[3] if user_data else 'free'
    paid_depts = user_data[4] if user_data else ''

    if user_id != ADMIN_ID and user_dept != subject_code:
        conn.close()
        err_msg = f"⚠️ ይቅርታ! እርስዎ የተመዘገቡት በ **{user_dept}** ስለሆነ የ **{subject_code}** ፈተና መፈተን አይችሉም።" if user_lang == 'am' else f"⚠️ Sorry! You are registered in **{user_dept}**, so you cannot take **{subject_code}** exams."
        await callback.message.answer(err_msg)
        return

    pay_key = f"{subject_code}_{full_exam_year}"
    is_paid_for_this = pay_status == 'paid' and pay_key in paid_depts.split(",")

    if not is_paid_for_this and (free_used >= 3 or offset_val >= 3):
        conn.close()
        await send_payment_prompt(callback.message, f"{subject_code} ({year_val} {month_val})", pay_key, user_lang)
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

        bm_text = "🔖 ማስቀመጫ (Bookmark)" if user_lang == 'am' else "🔖 Bookmark"
        menu_text = "🏠 ዋና ማውጫ" if user_lang == 'am' else "🏠 Main Menu"

        builder.row(
            types.InlineKeyboardButton(text=bm_text, callback_data=f"bm_{q_id}"),
            types.InlineKeyboardButton(text=menu_text, callback_data="back_menu")
        )

        q_num_display = offset_val + 1
        if user_lang == 'am':
            rem_text = f" (ቀሪ ነጻ ጥያቄ: {3 - free_used})" if not is_paid_for_this else " (VIP የተከፈተ 🌟)"
            score_display = f" | ውጤት: {current_score}/{offset_val}" if offset_val > 0 else ""
        else:
            rem_text = f" (Free Qs left: {3 - free_used})" if not is_paid_for_this else " (VIP Unlocked 🌟)"
            score_display = f" | Score: {current_score}/{offset_val}" if offset_val > 0 else ""

        await callback.message.answer(
            f"📝 **{subject_code} ({year_val} {month_val}) Exit Exam — Q{q_num_display}{score_display}{rem_text}:**\n\n{q_text}",
            reply_markup=builder.as_markup(), parse_mode="Markdown"
        )
    else:
        percentage = int((current_score / offset_val) * 100) if offset_val > 0 else 0
        builder = InlineKeyboardBuilder()
        menu_text = "🏠 ዋና ማውጫ" if user_lang == 'am' else "🏠 Main Menu"
        builder.row(types.InlineKeyboardButton(text=menu_text, callback_data="back_menu"))

        if user_lang == 'am':
            summary_text = (
                f"🎉 **እንኳን ደስ አለዎት!** በዚህ ምድብ ያሉትን ጥያቄዎች በሙሉ አጠናቀዋል።\n\n"
                f"📊 **የእርስዎ ውጤት:**\n"
                f"✅ ትክክለኛ መልሶች: **{current_score}/{offset_val}**\n"
                f"💯 መቶኛ: **{percentage}%**"
            )
        else:
            summary_text = (
                f"🎉 **Congratulations!** You have completed all questions in this category.\n\n"
                f"📊 **Final Score:**\n"
                f"✅ Correct Answers: **{current_score}/{offset_val}**\n"
                f"💯 Percentage: **{percentage}%**"
            )
        await callback.message.answer(summary_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 5. የክፍያ ጥያቄ ማሳያ[cite: 8]
async def send_payment_prompt(message: types.Message, dept_name: str, pay_key: str, lang: str):
    if lang == 'am':
        pay_text = (
            f"🔒 **3ቱን ነጻ ጥያቄዎች ጨርሰዋል!**\n\n"
            f"🎓 ለ **{dept_name}** ሙሉ ጥያቄዎች እና ማብራሪያዎች ክፍያ መፈጸም አለብዎት።\n"
            f"💰 **ክፍያው 50 Birr ብቻ ነው!**\n\n"
            f"ኦፊሴላዊ የክፍያ አካውንቶች:\n\n"
            f"🏦 **ኢትዮጵያ ንግድ ባንክ (CBE):** `1000268717823` (ነጋሽ ወንዴ)\n"
            f"📱 **ቴሌብር (Telebirr):** `0919245693` (ነጋሽ ወንዴ)\n\n"
            f"📸 ክፍያ ከፈጸሙ በኋላ የክፍያ ማረጋገጫ (Screenshot) ፎቶ ወደዚህ ቦት ይላኩ!"
        )
        btn_screenshot = "📤 ስክሪንሾት ላክ (አድሚን እንዲያይ)"
        btn_menu = "🏠 ዋና ማውጫ"
    else:
        pay_text = (
            f"🔒 **You have used your 3 free questions!**\n\n"
            f"🎓 Please make a payment to unlock full questions and explanations for **{dept_name}**.\n"
            f"💰 **Fee: 50 Birr only!**\n\n"
            f"Official payment accounts:\n\n"
            f"🏦 **CBE (Commercial Bank of Ethiopia):** `1000268717823` (Negash Wonde)\n"
            f"📱 **Telebirr:** `0919245693` (Negash Wonde)\n\n"
            f"📸 Send your payment screenshot to this bot after paying!"
        )
        btn_screenshot = "📤 Send Screenshot (Admin)"
        btn_menu = "🏠 Main Menu"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=btn_screenshot, callback_data=f"upload_screenshot_info_{pay_key}"))
    builder.row(types.InlineKeyboardButton(text=btn_menu, callback_data="back_menu"))
    await message.answer(pay_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("upload_screenshot_info_"))
async def screenshot_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📸 እባክዎ የክፍያ ማረጋገጫ (Screenshot) ምስል በቀጥታ በዚህ ቻት ውስጥ ፎቶውን ይላኩ። አድሚኑ ወዲያውኑ አረጋግጦ ይከፍትልዎታል! / Please send your payment screenshot photo directly in this chat.")


# 6. ተማሪው ስክሪንሾት ሲልክ
@dp.message(F.photo)
async def handle_payment_screenshot(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    photo_id = message.photo[-1].file_id

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
    builder.row(types.InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"rej_{user_id}"))

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
        builder.row(types.InlineKeyboardButton(text="🏠 ዋና ማውጫ", callback_data="back_menu"))
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


# 7. መልስ ማረጋገጫ እና Score ማስቀጠያ ሎጂክ
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
            result_text = "✅ **Correct!**"
            cursor.execute(
                "UPDATE user_progress SET total_attempted = total_attempted + 1, correct_count = correct_count + 1 WHERE user_id = ?",
                (user_id,))
        else:
            result_text = f"❌ **Incorrect. Correct answer: {correct}**"
            cursor.execute(
                "UPDATE user_progress SET total_attempted = total_attempted + 1, wrong_count = wrong_count + 1 WHERE user_id = ?",
                (user_id,))
        conn.commit()

    conn.close()

    next_offset = offset_val + 1
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="➡️ Next Question",
                                           callback_data=f"start_exam_{subject_code}_{year_val}_{month_val}_{next_offset}_{current_score}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))

    feedback = f"{result_text}\n\n💡 **Explanation:**\n{explanation}"
    await callback.message.answer(feedback, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 8. Bookmark
@dp.callback_query(F.data.startswith("bm_"))
async def bookmark_question(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    q_id = int(callback.data.split("_")[1])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO bookmarks (user_id, question_id) VALUES (?, ?)", (user_id, q_id))
        conn.commit()
        await callback.answer("✅ Added to Bookmarks!", show_alert=True)
    except sqlite3.IntegrityError:
        await callback.answer("ℹ️ Already bookmarked!", show_alert=True)
    conn.close()


# 9. Bookmarks List
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
        bm_text = "🔖 **Bookmarked Questions:**\n\n"
        for bm in bookmarks:
            q_id, subj, year, q_text = bm
            bm_text += f"📌 ID: {q_id} | [{subj} - {year}]\n{q_text[:50]}...\n\n"
            builder.row(types.InlineKeyboardButton(text=f"🔍 View Question #{q_id}",
                                                   callback_data=f"ans_{subj}_{year.split('_')[0]}_{year.split('_')[1]}_0_{q_id}_0_A"))
    else:
        bm_text = "🔖 No bookmarks saved yet."

    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(bm_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


# 10. Progress
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
        f"📊 **My Progress:**\n\n"
        f"📝 Total Attempted: **{total}**\n"
        f"✅ Correct: **{correct}**\n"
        f"❌ Wrong: **{wrong}**"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(progress_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


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

    text_msg = "🎓 **Documents (PPT/PDF) - Categories**\n\nSelect a category:"
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
    await show_main_menu(callback, callback.from_user.id, callback.from_user.first_name, edit=True)


async def main():
    init_db()
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("🌐 Flask Web Server & Mini App API started successfully on port 8080")
    print("🚀 WanK Exam Bot is running live!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())