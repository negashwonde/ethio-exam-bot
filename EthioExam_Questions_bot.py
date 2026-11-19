import asyncio
import logging
import os
from threading import Thread

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from flask import Flask, jsonify, render_template_string, request

from import_questions import get_conn, load_all_exam_datasets

app = Flask(__name__)
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://ethio-exam-bot-882d.onrender.com/webapp")
DOCS_CHANNEL_URL = os.environ.get("DOCS_CHANNEL_URL", "https://t.me/NegashComputerTips/264")

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
            background: rgba(30, 41, 59, 0.92);
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
        .btn:hover { opacity: 0.92; }
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
        .correct { background-color: #16a34a !important; border-color: #22c55e !important; }
        .incorrect { background-color: #dc2626 !important; border-color: #ef4444 !important; }
        .hidden { display: none; }
        .info-box { font-size: 14px; color: #93c5fd; margin-bottom: 10px; line-height: 1.4; }
        .badge-free {
            display: inline-block;
            background: #0f766e;
            color: #ccfbf1;
            padding: 3px 8px;
            border-radius: 999px;
            font-size: 12px;
            margin-left: 6px;
        }
        .badge-vip {
            display: inline-block;
            background: #b45309;
            color: #fef3c7;
            padding: 3px 8px;
            border-radius: 999px;
            font-size: 12px;
            margin-left: 6px;
        }
        a.doc-link {
            color: #38bdf8;
            word-break: break-all;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>🎓 Wank Exam Portal</h1>
    <p id="user-greeting" style="color: #cbd5e1; font-size: 14px;">ሰላም!</p>

    <div id="menu-view" class="card">
        <div class="info-box">👇 ከታች ከሚገኙት አማራጮች ውስጥ የሚፈልጉትን ይምረጡ (በእያንዳንዱ ኮርስ 3 ነጻ ጥያቄዎች):</div>
        <button class="btn" onclick="showSubMenu('CS')">💻 Computer Science Exit Exam</button>
        <button class="btn" onclick="showSubMenu('IT')">📚 Information Technology Exit Exam</button>
        <button class="btn" onclick="showFreshmanMenu()">📚 Freshman Program (Natural)</button>
        <button class="btn" onclick="showSocialFreshmanMenu()">📚 Freshman Program (Social)</button>
        <button class="btn" onclick="alert('📖 Remedial program exams and materials will be updated soon!')">📖 Remedial Program</button>
        <button class="btn" onclick="alert('📊 የርስዎን ውጤት ለማየት ዋናውን የቴሌግራም ቦት ይጠቀሙ።')">📊 የእኔ ውጤት (My Progress)</button>
        <button class="btn" onclick="showDocsView()">📄 ሰነዶች (ማቴሪያሎች)</button>
        <button class="btn" onclick="alert('ℹ️ WankExamBot ለሁሉም የዩኒቨርሲቲ ተማሪዎች የተዘጋጀ የዝግጅት ረዳት ነው።')">ℹ️ ስለ ቦቱ (About Bot)</button>
        <button class="btn" onclick="alert('🎧 እርዳታ ለማግኘት በስልክ ቁጥር 0919245693 ወይም @neguRoha ያግኙን።')">🎧 እርዳታ እና ድጋፍ (Support)</button>
    </div>

    <div id="docs-view" class="card hidden">
        <h3 style="color: #38bdf8;">📄 ሰነዶች እና ማቴሪያሎች</h3>
        <div class="info-box">
            ለሁሉም ዲፓርትመንቶች የተዘጋጁ የExit Exam እና Freshman ማስታወሻዎችና ሰነዶች እዚህ ይገኛሉ:<br><br>
            🔗 ዋና ማቴሪያል ሊንክ:<br>
            <a class="doc-link" href="https://t.me/NegashComputerTips/264" target="_blank">https://t.me/NegashComputerTips/264</a>
        </div>
        <div id="docs-list" style="font-size: 13px; color: #e2e8f0; margin-bottom: 12px;"></div>
        <button class="btn" onclick="backToMenu()" style="background: #475569; text-align: center;">🏠 ዋና ማውጫ (Main Menu)</button>
    </div>

    <div id="submenu-view" class="card hidden">
        <h3 id="submenu-title" style="color: #38bdf8;">Select exam year and month:</h3>
        <button class="btn" onclick="startExam(selectedSubject, '2017 ጥር')">📅 2017 ጥር</button>
        <button class="btn" onclick="startExam(selectedSubject, '2017 ሰኔ')">📅 2017 ሰኔ</button>
        <button class="btn" onclick="startExam(selectedSubject, '2018 ጥር')">📅 2018 ጥር</button>
        <button class="btn" onclick="startExam(selectedSubject, '2018 ሰኔ')">📅 2018 ሰኔ</button>
        <button class="btn" onclick="backToMenu()" style="background: #475569; margin-top: 15px;">🏠 ዋና ማውጫ (Main Menu)</button>
    </div>

    <div id="freshman-view" class="card hidden">
        <h3 style="color: #38bdf8;">📚 Freshman Program (Natural Science)</h3>
        <div class="info-box">👇 የሚፈልጉትን ኮርስ ይምረጡ:</div>
        <button class="btn" onclick="startExam('Freshman', 'Psychology')">🧠 General Psychology</button>
        <button class="btn" onclick="startExam('Freshman', 'Geography')">🌍 Geography of Ethiopia & the Horn</button>
        <button class="btn" onclick="startExam('Freshman', 'Logic')">⚖️ Logic & Critical Thinking</button>
        <button class="btn" onclick="startExam('Freshman', 'English')">🗣️ Communicative English Skills</button>
        <button class="btn" onclick="startExam('Freshman', 'Physics')">⚛️ General Physics</button>
        <button class="btn" onclick="startExam('Freshman', 'Inclusiveness')">🤝 Inclusiveness</button>
        <button class="btn" onclick="startExam('Freshman', 'Math')">📐 Mathematics for Natural Sciences</button>
        <button class="btn" onclick="backToMenu()" style="background: #475569; margin-top: 15px;">🏠 ዋና ማውጫ (Main Menu)</button>
    </div>

    <div id="freshman-social-view" class="card hidden">
        <h3 style="color: #38bdf8;">📚 Freshman Program (Social Science)</h3>
        <div class="info-box">👇 የሚፈልጉትን ኮርስ ይምረጡ:</div>
        <button class="btn" onclick="startExam('Freshman_Social', 'Anthropology')">🏛️ Social Anthropology</button>
        <button class="btn" onclick="startExam('Freshman_Social', 'Geography')">🌍 Geography of Ethiopia & the Horn</button>
        <button class="btn" onclick="startExam('Freshman_Social', 'History')">📜 History of Ethiopia & the Horn</button>
        <button class="btn" onclick="startExam('Freshman_Social', 'Logic')">⚖️ Logic & Critical Thinking</button>
        <button class="btn" onclick="startExam('Freshman_Social', 'Civics')">🗳️ Civics and Ethical Studies</button>
        <button class="btn" onclick="startExam('Freshman_Social', 'Global_Trends')">🌐 Global Trends</button>
        <button class="btn" onclick="backToMenu()" style="background: #475569; margin-top: 15px;">🏠 ዋና ማውጫ (Main Menu)</button>
    </div>

    <div id="exam-view" class="card hidden">
        <div id="q-header" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
            <h3 id="q-title" style="color: #38bdf8; margin:0;">ጥያቄ</h3>
            <span id="q-badge"></span>
        </div>
        <p id="q-text" style="font-size: 15px; line-height: 1.5; margin-top:12px;"></p>

        <button class="opt-btn" id="btn-a" onclick="submitAnswer('A')"></button>
        <button class="opt-btn" id="btn-b" onclick="submitAnswer('B')"></button>
        <button class="opt-btn" id="btn-c" onclick="submitAnswer('C')"></button>
        <button class="opt-btn" id="btn-d" onclick="submitAnswer('D')"></button>

        <p id="explanation" style="margin-top: 15px; font-size: 14px; color: #38bdf8;"></p>
        <button id="next-btn" class="btn hidden" onclick="loadNextQuestion()" style="text-align: center;">ቀጣይ ጥያቄ ➡️</button>
        <button class="btn" onclick="backToMenu()" style="background: #475569; text-align: center; margin-top: 10px;">🏠 ዋና ማውጫ</button>
    </div>

    <div id="payment-view" class="card hidden" style="text-align: center;">
        <h2 style="color: #f87171;">🔒 የመጀመሪያዎቹን 3 ነጻ ጥያቄዎች ጨርሰዋል!</h2>
        <p style="font-size: 14px; line-height: 1.6; text-align: left; background: #1e293b; padding: 12px; border-radius: 8px;">
            🎓 ለዚህ ኮርስ <b>ሙሉ ጥያቄዎችን (Full Questions)</b> ለመፈተን ክፍያ መፈጸም አለብዎት።<br>
            💰 <b>ክፍያው 100 Birr ብቻ ነው!</b><br><br>
            🏦 <b>CBE:</b> <code>1000268717823</code> (ነጋሽ ወንዴ)<br>
            📱 <b>Telebirr:</b> <code>0919245693</code> (ነጋሽ ወንዴ)<br><br>
            📸 <b>ክፍያ ከፈጸሙ በኋላ ስክሪንሾቱን በቀጥታ ወደ ቴሌግራም ቦቱ ይላኩ! አድሚኑ ሲያጸድቅልዎ ሙሉ ጥያቄዎች ይከፈታሉ።</b>
        </p>
        <button class="btn" onclick="startExam(selectedSubject, currentYear)" style="background: #059669; text-align: center;">🔄 ክፍያ ጸድቋል? እንደገና ሞክር</button>
        <button class="btn" onclick="backToMenu()" style="text-align: center;">🏠 ዋና ማውጫ ተመለስ</button>
    </div>

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

        let selectedSubject = '';
        let currentYear = '';
        let questionsList = [];
        let currentIndex = 0;
        let score = 0;
        let isPaidUser = false;
        const FREE_LIMIT = 3;

        function hideAllViews() {
            ['menu-view', 'docs-view', 'submenu-view', 'freshman-view', 'freshman-social-view', 'exam-view', 'payment-view', 'result-view']
                .forEach(id => document.getElementById(id).classList.add('hidden'));
        }

        function showDocsView() {
            hideAllViews();
            document.getElementById('docs-view').classList.remove('hidden');
            fetch('/api/documents')
                .then(res => res.json())
                .then(data => {
                    const listEl = document.getElementById('docs-list');
                    const docs = data.documents || [];
                    if (docs.length === 0) {
                        listEl.innerHTML = '<div>📌 ተጨማሪ ሰነዶች ሲታከሉ እዚህ ይታያሉ።</div>';
                        return;
                    }
                    listEl.innerHTML = docs.map(d =>
                        `<div style="background:#1e293b;padding:8px;border-radius:6px;margin-bottom:6px;">
                            <b>${d.title}</b> (${d.department})<br>
                            ${d.url ? `<a class="doc-link" href="${d.url}" target="_blank">${d.url}</a>` : `<span>File: ${d.file_name}</span>`}
                        </div>`
                    ).join('');
                })
                .catch(() => {});
        }

        function showSubMenu(subj) {
            selectedSubject = subj;
            hideAllViews();
            document.getElementById('submenu-title').innerText = `${subj === 'CS' ? 'Computer Science' : 'Information Technology'} Exit Exam\nSelect exam year and month:`;
            document.getElementById('submenu-view').classList.remove('hidden');
        }

        function showFreshmanMenu() {
            hideAllViews();
            document.getElementById('freshman-view').classList.remove('hidden');
        }

        function showSocialFreshmanMenu() {
            hideAllViews();
            document.getElementById('freshman-social-view').classList.remove('hidden');
        }

        function startExam(subj, yearMonth) {
            selectedSubject = subj;
            currentYear = yearMonth;
            fetch(`/api/questions?subject=${encodeURIComponent(subj)}&year=${encodeURIComponent(yearMonth)}&user_id=${userId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.locked) {
                        hideAllViews();
                        document.getElementById('payment-view').classList.remove('hidden');
                        return;
                    }
                    questionsList = data.questions || [];
                    isPaidUser = Boolean(data.is_paid);
                    if (questionsList.length === 0) {
                        alert("⚠️ በዚህ ምድብ ጥያቄዎች አልተገኙም!");
                        return;
                    }
                    currentIndex = 0;
                    score = 0;
                    hideAllViews();
                    document.getElementById('exam-view').classList.remove('hidden');
                    showQuestion();
                });
        }

        function showQuestion() {
            if (!isPaidUser && currentIndex >= FREE_LIMIT) {
                hideAllViews();
                document.getElementById('payment-view').classList.remove('hidden');
                return;
            }

            if (currentIndex >= questionsList.length) {
                hideAllViews();
                document.getElementById('result-view').classList.remove('hidden');
                const pct = Math.round((score / questionsList.length) * 100);
                document.getElementById('final-score').innerText = `📊 ትክክለኛ መልሶች: ${score} ከ ${questionsList.length} (${pct}%)`;
                return;
            }

            let q = questionsList[currentIndex];
            document.getElementById('q-title').innerText = `📝 ጥያቄ ${currentIndex + 1} / ${questionsList.length}`;
            document.getElementById('q-badge').innerHTML = isPaidUser
                ? `<span class="badge-vip">VIP ሙሉ ፈተና</span>`
                : `<span class="badge-free">ነጻ (${FREE_LIMIT - currentIndex} ቀርቷል)</span>`;

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
                body: JSON.stringify({
                    user_id: userId,
                    question_id: q.id,
                    selected: selectedOpt,
                    subject: selectedSubject,
                    year: currentYear,
                    step_index: currentIndex
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.locked) {
                    hideAllViews();
                    document.getElementById('payment-view').classList.remove('hidden');
                    return;
                }
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
            hideAllViews();
            document.getElementById('menu-view').classList.remove('hidden');
        }
    </script>
</body>
</html>
"""

TOPIC_KEYS = {
    "cs17t": ("CS", "2017 ጥር"),
    "cs17s": ("CS", "2017 ሰኔ"),
    "cs18t": ("CS", "2018 ጥር"),
    "cs18s": ("CS", "2018 ሰኔ"),
    "it17t": ("IT", "2017 ጥር"),
    "it17s": ("IT", "2017 ሰኔ"),
    "it18t": ("IT", "2018 ጥር"),
    "it18s": ("IT", "2018 ሰኔ"),
    "fn_psy": ("Freshman", "Psychology"),
    "fn_geo": ("Freshman", "Geography"),
    "fn_log": ("Freshman", "Logic"),
    "fn_eng": ("Freshman", "English"),
    "fn_phy": ("Freshman", "Physics"),
    "fn_inc": ("Freshman", "Inclusiveness"),
    "fn_mat": ("Freshman", "Math"),
    "fs_ant": ("Freshman_Social", "Anthropology"),
    "fs_geo": ("Freshman_Social", "Geography"),
    "fs_his": ("Freshman_Social", "History"),
    "fs_log": ("Freshman_Social", "Logic"),
    "fs_civ": ("Freshman_Social", "Civics"),
    "fs_glb": ("Freshman_Social", "Global_Trends"),
    "rem_all": ("Remedial", "All"),
}

KEY_BY_PAIR = {v: k for k, v in TOPIC_KEYS.items()}


def init_documents_table():
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT DEFAULT 'ALL',
                title TEXT NOT NULL,
                file_id TEXT DEFAULT '',
                file_name TEXT DEFAULT '',
                url TEXT DEFAULT ''
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def check_user_paid_for_topic(conn, user_id: int, subj: str, year: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT payment_status, paid_department FROM users WHERE user_id = ?", (user_id,))
    user_data = cur.fetchone()
    if not user_data:
        return False
    pay_status = (user_data[0] or "free").strip().lower()
    paid_depts = user_data[1] or ""
    if pay_status != "paid":
        return False

    paid_set = {x.strip() for x in paid_depts.split(",") if x.strip()}
    pay_key = f"{subj}_{year}"
    t_code = KEY_BY_PAIR.get((subj, year), "")
    return (
        pay_key in paid_set
        or (t_code and t_code in paid_set)
        or subj in paid_set
        or "ALL" in paid_set
    )


def get_questions_for_pair(conn, subj: str, topic: str):
    cur = conn.cursor()
    if subj in ("Freshman", "Freshman_Social"):
        cur.execute(
            """
            SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation
            FROM questions
            WHERE subject = ? AND exam_year = ?
            ORDER BY id ASC
            """,
            (subj, topic),
        )
        rows = cur.fetchall()
        if not rows:
            cur.execute(
                """
                SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation
                FROM questions
                WHERE subject = ? AND exam_year LIKE ?
                ORDER BY id ASC
                """,
                (subj, f"%{topic}%"),
            )
            rows = cur.fetchall()
        return rows

    alt_topic = topic.replace("ጥር", "Tir").replace("ሰኔ", "Sane")
    cur.execute(
        """
        SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation
        FROM questions
        WHERE subject = ? AND (exam_year = ? OR exam_year LIKE ? OR exam_year LIKE ?)
        ORDER BY id ASC
        """,
        (subj, topic, f"%{topic}%", f"%{alt_topic}%"),
    )
    return cur.fetchall()


@app.route("/")
def home():
    return "🤖 WanK CS, IT & Freshman Exam Bot & Mini App API is running live!"


@app.route("/webapp")
def webapp():
    return render_template_string(MINI_APP_HTML)


@app.route("/api/documents")
def api_documents():
    init_documents_table()
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, department, title, file_name, url FROM documents ORDER BY id DESC LIMIT 20"
        ).fetchall()
        docs = [
            {"id": r[0], "department": r[1], "title": r[2], "file_name": r[3], "url": r[4]}
            for r in rows
        ]
        return jsonify({"channel_url": DOCS_CHANNEL_URL, "documents": docs})
    finally:
        conn.close()


@app.route("/api/questions")
def api_questions():
    subj = request.args.get("subject", "CS").strip()
    year = request.args.get("year", "2017 ጥር").strip()
    try:
        user_id = int(request.args.get("user_id", 0))
    except ValueError:
        user_id = 0

    conn = get_conn()
    try:
        is_paid = check_user_paid_for_topic(conn, user_id, subj, year)
        rows = get_questions_for_pair(conn, subj, year)
        if not rows:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation
                FROM questions
                WHERE subject = ?
                ORDER BY id ASC
                """,
                (subj,),
            )
            rows = cur.fetchall()

        if not rows:
            return jsonify({"locked": False, "is_paid": is_paid, "questions": []})

        selected_rows = rows if is_paid else rows[:3]

        questions = [
            {
                "id": r[0],
                "question_text": r[1],
                "option_a": r[2],
                "option_b": r[3],
                "option_c": r[4],
                "option_d": r[5],
                "correct_answer": r[6],
                "explanation": r[7],
            }
            for r in selected_rows
        ]
        return jsonify({"locked": False, "is_paid": is_paid, "total_available": len(rows), "questions": questions})
    finally:
        conn.close()


@app.route("/api/answer", methods=["POST"])
def api_answer():
    data = request.get_json(silent=True) or {}
    q_id = data.get("question_id")
    selected = data.get("selected")
    subj = (data.get("subject") or "CS").strip()
    year = (data.get("year") or "").strip()
    step_index = int(data.get("step_index") or 0)
    try:
        user_id = int(data.get("user_id") or 0)
    except ValueError:
        user_id = 0

    conn = get_conn()
    try:
        is_paid = check_user_paid_for_topic(conn, user_id, subj, year)
        if not is_paid and step_index >= 3:
            return jsonify({"locked": True, "is_correct": False, "correct_answer": "A"})

        cur = conn.cursor()
        cur.execute("SELECT correct_answer FROM questions WHERE id = ?", (q_id,))
        res = cur.fetchone()
        correct_ans = res[0] if res else "A"
        return jsonify({"is_correct": selected == correct_ans, "correct_answer": correct_ans, "locked": False})
    finally:
        conn.close()


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing!")

ADMIN_ID = int(os.environ.get("ADMIN_ID", "680798556"))
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
admin_selections = {}


async def show_main_menu(message_or_callback, user_id, user_name, edit=False):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT department, lang FROM users WHERE user_id = ?", (user_id,))
        user_data = cur.fetchone()
        if not user_data:
            cur.execute(
                """
                INSERT INTO users (user_id, department, lang, free_questions_used, payment_status, paid_department)
                VALUES (?, 'CS', 'am', 0, 'free', '')
                """,
                (user_id,),
            )
            conn.commit()
            user_lang = "am"
        else:
            user_lang = user_data[1] or "am"
    finally:
        conn.close()

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="🤖 ፈተናውን በ ሚኒ አፕ ክፈት" if user_lang == "am" else "🤖 Open Exam Mini App",
            web_app=types.WebAppInfo(url=WEBAPP_URL),
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="💻 ኮምፒውተር ሳይንስ >" if user_lang == "am" else "💻 Computer Science >",
            callback_data="dept_cs_menu",
        ),
        types.InlineKeyboardButton(
            text="📚 ኢንፎርሜሽን ቴክኖሎጂ >" if user_lang == "am" else "📚 Information Technology >",
            callback_data="dept_it_menu",
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📚 ፍሬሽማን (ናቹራል) >" if user_lang == "am" else "📚 Freshman (Natural) >",
            callback_data="dept_freshman_menu",
        ),
        types.InlineKeyboardButton(
            text="📚 ፍሬሽማን (ሶሻል) >" if user_lang == "am" else "📚 Freshman (Social) >",
            callback_data="dept_freshman_social_menu",
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📖 ሬሚዲያል >" if user_lang == "am" else "📖 Remedial >",
            callback_data="dept_remedial_menu",
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📊 የእኔ ውጤት >" if user_lang == "am" else "📊 My Progress >",
            callback_data="my_progress",
        ),
        types.InlineKeyboardButton(
            text="🔖 ያስቀመጧቸው >" if user_lang == "am" else "🔖 Bookmarks >",
            callback_data="my_bookmarks",
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📄 ሰነዶች (ማቴሪያሎች) >" if user_lang == "am" else "📄 Documents >",
            callback_data="tutorial_package",
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="⚙️ ዲፓርትመንት ቀይር" if user_lang == "am" else "⚙️ Change Dept",
            callback_data="change_dept_menu",
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="ℹ️ ስለ ቦቱ >" if user_lang == "am" else "ℹ️ About >",
            callback_data="about_bot",
        ),
        types.InlineKeyboardButton(
            text="🎧 እርዳታ እና ድጋፍ >" if user_lang == "am" else "🎧 Support >",
            callback_data="help_menu",
        ),
    )
    builder.row(
        types.InlineKeyboardButton(text="🇪🇹 አማርኛ", callback_data="set_lang_am"),
        types.InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en"),
    )

    welcome_text = (
        f"👋 **ሰላም {user_name}!**\n\n"
        f"🎓 **ወደ Wank Exam ዝግጅት ቦት እንኳን ደህና መጡ።**\n"
        f"ለኮምፒውተር ሳይንስ (CS)፣ ለአይቲ (IT) እና ለፍሬሽማን የፈተና ጥያቄዎች እዚህ ያገኛሉ።\n\n"
        f"💡 *ማሳሰቢያ:* እያንዳንዱ ኮርስ ላይ የመጀመሪያዎቹ **3 ጥያቄዎች በነጻ** መፈተን ይችላሉ!\n\n"
        f"👇 ከታች ከሚገኙት አማራጮች ውስጥ የሚፈልጉትን ይምረጡ:"
    )
    if edit:
        await message_or_callback.message.edit_text(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message_or_callback.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await show_main_menu(message, message.from_user.id, message.from_user.first_name, edit=False)


@dp.message(Command("adddoc"))
async def cmd_add_doc(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ ይህ ትዕዛዝ ለአድሚኑ ብቻ ነው።")
        return
    raw_args = message.text.replace("/adddoc", "", 1).strip()
    parts = [p.strip() for p in raw_args.split("|")]
    title = parts[0] if len(parts) >= 1 and parts[0] else "Exit Exam & Freshman Material"
    url = parts[1] if len(parts) >= 2 and parts[1] else DOCS_CHANNEL_URL
    dept = parts[2] if len(parts) >= 3 and parts[2] else "ALL"

    init_documents_table()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO documents (department, title, file_id, file_name, url) VALUES (?, ?, '', '', ?)",
            (dept, title, url),
        )
        conn.commit()
    finally:
        conn.close()

    await message.answer(
        f"✅ ሰነዱ ተመዝግቧል!\n• ርዕስ: **{title}**\n• ዲፓርትመንት: **{dept}**\n• ሊንክ: {url}",
        parse_mode="Markdown",
    )


@dp.message(F.document)
async def handle_admin_document_upload(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("📄 ሰነዶችን ለማየት ከዋና ማውጫ **ሰነዶች (ማቴሪያሎች)** የሚለውን ይጫኑ።")
        return

    doc = message.document
    title = (message.caption or doc.file_name or "Study Material").strip()
    init_documents_table()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO documents (department, title, file_id, file_name, url) VALUES (?, ?, ?, ?, ?)",
            ("ALL", title, doc.file_id, doc.file_name or "", DOCS_CHANNEL_URL),
        )
        conn.commit()
    finally:
        conn.close()

    await message.answer(
        f"✅ ሰነዱ ለሁሉም ዲፓርትመንት ተመዝግቧል!\n• ፋይል: `{doc.file_name}`\n• ርዕስ: **{title}**",
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "back_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await show_main_menu(callback, callback.from_user.id, callback.from_user.first_name, edit=True)


@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    new_lang = callback.data.split("_")[2]
    conn = get_conn()
    try:
        conn.execute("UPDATE users SET lang = ? WHERE user_id = ?", (new_lang, user_id))
        conn.commit()
    finally:
        conn.close()
    await callback.answer("Language changed!")
    await show_main_menu(callback, user_id, callback.from_user.first_name, edit=True)


@dp.callback_query(F.data == "change_dept_menu")
async def change_dept_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="💻 Computer Science (CS)", callback_data="set_dept_CS"),
        types.InlineKeyboardButton(text="📡 Information Technology (IT)", callback_data="set_dept_IT"),
    )
    builder.row(
        types.InlineKeyboardButton(text="📚 Freshman (Natural)", callback_data="set_dept_Freshman"),
        types.InlineKeyboardButton(text="📚 Freshman (Social)", callback_data="set_dept_Freshman_Social"),
    )
    builder.row(types.InlineKeyboardButton(text="📖 Remedial", callback_data="set_dept_Remedial"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "🎯 **እባክዎ ዲፓርትመንትዎን ይምረጡ:**", reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("set_dept_"))
async def set_department_action(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    selected_dept = callback.data.replace("set_dept_", "", 1)
    conn = get_conn()
    try:
        conn.execute("UPDATE users SET department = ? WHERE user_id = ?", (selected_dept, user_id))
        conn.commit()
    finally:
        conn.close()
    await callback.answer("✅ Department changed!", show_alert=True)
    await show_main_menu(callback, user_id, callback.from_user.first_name, edit=True)


@dp.callback_query(F.data == "dept_cs_menu")
async def cs_years_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 2017 ጥር", callback_data="q_cs17t_0_0"),
        types.InlineKeyboardButton(text="📅 2017 ሰኔ", callback_data="q_cs17s_0_0"),
    )
    builder.row(
        types.InlineKeyboardButton(text="📅 2018 ጥር", callback_data="q_cs18t_0_0"),
        types.InlineKeyboardButton(text="📅 2018 ሰኔ", callback_data="q_cs18s_0_0"),
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "💻 **Computer Science Exit Exam**\n\nSelect exam period:", reply_markup=builder.as_markup(), parse_mode="Markdown"
    )


@dp.callback_query(F.data == "dept_it_menu")
async def it_years_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 2017 ጥር", callback_data="q_it17t_0_0"),
        types.InlineKeyboardButton(text="📅 2017 ሰኔ", callback_data="q_it17s_0_0"),
    )
    builder.row(
        types.InlineKeyboardButton(text="📅 2018 ጥር", callback_data="q_it18t_0_0"),
        types.InlineKeyboardButton(text="📅 2018 ሰኔ", callback_data="q_it18s_0_0"),
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📡 **Information Technology (IT) Exit Exam**\n\nSelect exam period:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "dept_freshman_menu")
async def freshman_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 General Psychology", callback_data="q_fn_psy_0_0"))
    builder.row(types.InlineKeyboardButton(text="🌍 Geography of Ethiopia & the Horn", callback_data="q_fn_geo_0_0"))
    builder.row(types.InlineKeyboardButton(text="⚖️ Logic & Critical Thinking", callback_data="q_fn_log_0_0"))
    builder.row(types.InlineKeyboardButton(text="🗣️ Communicative English Skills", callback_data="q_fn_eng_0_0"))
    builder.row(types.InlineKeyboardButton(text="⚛️ General Physics", callback_data="q_fn_phy_0_0"))
    builder.row(types.InlineKeyboardButton(text="🤝 Inclusiveness", callback_data="q_fn_inc_0_0"))
    builder.row(types.InlineKeyboardButton(text="📐 Mathematics for Natural Sciences", callback_data="q_fn_mat_0_0"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📚 **Freshman Program (Natural Science)**\n\n👇 የሚፈልጉትን ኮርስ ይምረጡ:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "dept_freshman_social_menu")
async def freshman_social_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏛️ Social Anthropology", callback_data="q_fs_ant_0_0"))
    builder.row(types.InlineKeyboardButton(text="🌍 Geography of Ethiopia & the Horn", callback_data="q_fs_geo_0_0"))
    builder.row(types.InlineKeyboardButton(text="📜 History of Ethiopia & the Horn", callback_data="q_fs_his_0_0"))
    builder.row(types.InlineKeyboardButton(text="⚖️ Logic & Critical Thinking", callback_data="q_fs_log_0_0"))
    builder.row(types.InlineKeyboardButton(text="🗳️ Civics and Ethical Studies", callback_data="q_fs_civ_0_0"))
    builder.row(types.InlineKeyboardButton(text="🌐 Global Trends", callback_data="q_fs_glb_0_0"))
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📚 **Freshman Program (Social Science)**\n\n👇 የሚፈልጉትን ኮርስ ይምረጡ:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "dept_remedial_menu")
async def remedial_menu(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.edit_text(
        "📖 **Remedial Program**\n\nMaterials and exams will be updated soon!",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "my_progress")
async def show_my_progress(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT total_attempted, correct_count, wrong_count FROM user_progress WHERE user_id = ?",
            (user_id,),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    attempted, correct, wrong = row if row else (0, 0, 0)
    acc = int((correct / attempted) * 100) if attempted > 0 else 0
    text = (
        f"📊 **የእኔ ውጤት (My Progress)**\n\n"
        f"📝 የተሞከሩ ጥያቄዎች: **{attempted}**\n"
        f"✅ ትክክለኛ መልሶች: **{correct}**\n"
        f"❌ የተሳሳቱ መልሶች: **{wrong}**\n"
        f"🎯 ትክክለኛነት: **{acc}%**"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 ዋና ማውጫ", callback_data="back_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data == "my_bookmarks")
async def show_my_bookmarks(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT q.id, q.subject, q.exam_year, q.question_text, q.correct_answer
            FROM bookmarks b
            JOIN questions q ON b.question_id = q.id
            WHERE b.user_id = ?
            ORDER BY q.id DESC LIMIT 10
            """,
            (user_id,),
        )
        items = cur.fetchall()
    finally:
        conn.close()

    if not items:
        text = "🔖 **ያስቀመጧቸው ጥያቄዎች**\n\nእስካሁን የተቀመጠ ጥያቄ የለም። በፈተና ወቅት `🔖 Bookmark` ይጫኑ።"
    else:
        lines = ["🔖 **ያስቀመጧቸው ጥያቄዎች (የመጨረሻዎቹ 10):**\n"]
        for q_id, subj, yr, q_txt, ans in items:
            short_q = q_txt[:90] + ("..." if len(q_txt) > 90 else "")
            lines.append(f"• *[{subj} - {yr}]* #{q_id}: {short_q} (**መልስ: {ans}**)")
        text = "\n".join(lines)

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 ዋና ማውጫ", callback_data="back_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data == "tutorial_package")
async def tutorial_package_menu(callback: types.CallbackQuery):
    await callback.answer()
    init_documents_table()
    conn = get_conn()
    try:
        docs = conn.execute(
            "SELECT title, file_id, url FROM documents ORDER BY id DESC LIMIT 10"
        ).fetchall()
    finally:
        conn.close()

    lines = [
        "📄 **ሰነዶች እና ማቴሪያሎች**\n",
        f"🔗 **የExit Exam እና Freshman ሰነዶች ሊንክ:**\n{DOCS_CHANNEL_URL}\n",
    ]
    if docs:
        lines.append("📚 **የተጨመሩ ሰነዶች:**")
        for title, _, url in docs:
            link_part = f" — {url}" if url else ""
            lines.append(f"• **{title}**{link_part}")
    else:
        lines.append("የExit Exam እና Freshman ማስታወሻዎች ከላይ ባለው ሊንክ ይገኛሉ።")

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📂 ማቴሪያሎችን ክፈት", url=DOCS_CHANNEL_URL))
    for title, file_id, _ in docs:
        if file_id:
            try:
                await callback.message.answer_document(document=file_id, caption=f"📄 {title}")
            except Exception as e:
                logging.error(f"Send document error: {e}")

    builder.row(types.InlineKeyboardButton(text="🏠 ዋና ማውጫ", callback_data="back_menu"))
    await callback.message.edit_text("\n".join(lines), reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.in_({"about_bot", "help_menu"}))
async def info_menus(callback: types.CallbackQuery):
    await callback.answer()
    texts = {
        "about_bot": "ℹ️ **ስለ Wank Exam Bot**\n\nለCS፣ IT እና Freshman ተማሪዎች የተዘጋጀ የልምምድ ቦት እና ሚኒ አፕ ነው።",
        "help_menu": "🎧 **እርዳታ እና ድጋፍ**\n\n📞 ስልክ: `0919245693`\n👤 ቴሌግራም: `@neguRoha`",
    }
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 ዋና ማውጫ", callback_data="back_menu"))
    await callback.message.edit_text(texts[callback.data], reply_markup=builder.as_markup(), parse_mode="Markdown")


async def send_payment_prompt(message: types.Message, dept_name: str, pay_key: str):
    pay_text = (
        f"🔒 **የመጀመሪያዎቹን 3 ነጻ ጥያቄዎች ጨርሰዋል!**\n\n"
        f"🎓 ለ **{dept_name}** ተጨማሪ ጥያቄዎች ክፍያ መፈጸም አለብዎት።\n"
        f"💰 **ክፍያው 100 Birr ብቻ ነው!**\n\n"
        f"🏦 **CBE:** `1000268717823` (ነጋሽ ወንዴ)\n"
        f"📱 **Telebirr:** `0919245693` (ነጋሽ ወንዴ)\n\n"
        f"📸 ክፍያ ከፈጸሙ በኋላ ስክሪንሾቱን ወደዚህ ቦት ይላኩ!"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📤 ስክሪንሾት ላክ", callback_data=f"up_ss_{pay_key[:35]}"))
    builder.row(types.InlineKeyboardButton(text="🏠 ዋና ማውጫ", callback_data="back_menu"))
    await message.answer(pay_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("up_ss_"))
async def screenshot_info(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("📸 እባክዎ የክፍያ ማረጋገጫ (Screenshot) ምስል በቀጥታ በዚህ ቻት ውስጥ ፎቶውን ይላኩ።")


@dp.message(F.photo)
async def handle_payment_screenshot(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    photo_id = message.photo[-1].file_id

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT department FROM users WHERE user_id = ?", (user_id,))
        res = cur.fetchone()
    finally:
        conn.close()
    student_dept = res[0] if res else "Unknown"

    await message.answer("📥 **የክፍያ ስክሪንሾትዎ ደርሷል!** አድሚኑ እስኪያረጋግጠው ይጠብቁ።", parse_mode="Markdown")

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="☑️ CS - 2017 ጥር", callback_data=f"tg_{user_id}_cs17t"),
        types.InlineKeyboardButton(text="☑️ CS - 2017 ሰኔ", callback_data=f"tg_{user_id}_cs17s"),
    )
    builder.row(
        types.InlineKeyboardButton(text="☑️ CS - 2018 ጥር", callback_data=f"tg_{user_id}_cs18t"),
        types.InlineKeyboardButton(text="☑️ CS - 2018 ሰኔ", callback_data=f"tg_{user_id}_cs18s"),
    )
    builder.row(
        types.InlineKeyboardButton(text="☑️ IT - 2017 ጥር", callback_data=f"tg_{user_id}_it17t"),
        types.InlineKeyboardButton(text="☑️ IT - 2017 ሰኔ", callback_data=f"tg_{user_id}_it17s"),
    )
    builder.row(
        types.InlineKeyboardButton(text="☑️ IT - 2018 ጥር", callback_data=f"tg_{user_id}_it18t"),
        types.InlineKeyboardButton(text="☑️ IT - 2018 ሰኔ", callback_data=f"tg_{user_id}_it18s"),
    )
    builder.row(
        types.InlineKeyboardButton(text="🧠 Psych", callback_data=f"tg_{user_id}_fn_psy"),
        types.InlineKeyboardButton(text="🌍 Geog (Nat)", callback_data=f"tg_{user_id}_fn_geo"),
    )
    builder.row(
        types.InlineKeyboardButton(text="⚖️ Logic (Nat)", callback_data=f"tg_{user_id}_fn_log"),
        types.InlineKeyboardButton(text="🗣️ English", callback_data=f"tg_{user_id}_fn_eng"),
    )
    builder.row(
        types.InlineKeyboardButton(text="⚛️ Physics", callback_data=f"tg_{user_id}_fn_phy"),
        types.InlineKeyboardButton(text="🤝 Inclusiv.", callback_data=f"tg_{user_id}_fn_inc"),
    )
    builder.row(
        types.InlineKeyboardButton(text="📐 Math (Nat)", callback_data=f"tg_{user_id}_fn_mat"),
        types.InlineKeyboardButton(text="🏛️ Anthrop", callback_data=f"tg_{user_id}_fs_ant"),
    )
    builder.row(
        types.InlineKeyboardButton(text="🌍 Geog (Soc)", callback_data=f"tg_{user_id}_fs_geo"),
        types.InlineKeyboardButton(text="📜 History", callback_data=f"tg_{user_id}_fs_his"),
    )
    builder.row(
        types.InlineKeyboardButton(text="⚖️ Logic (Soc)", callback_data=f"tg_{user_id}_fs_log"),
        types.InlineKeyboardButton(text="🗳️ Civics", callback_data=f"tg_{user_id}_fs_civ"),
    )
    builder.row(
        types.InlineKeyboardButton(text="🌐 Global Tr", callback_data=f"tg_{user_id}_fs_glb"),
        types.InlineKeyboardButton(text="📖 Remedial", callback_data=f"tg_{user_id}_rem_all"),
    )
    builder.row(types.InlineKeyboardButton(text="🚀 አጽድቅ (Approve)", callback_data=f"fapp_{user_id}"))
    builder.row(types.InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"rej_{user_id}"))

    admin_caption = (
        f"🔔 አዲስ ክፍያ መጥቷል! (100 Birr)\n\n"
        f"👤 ስም: {user_name}\n"
        f"🎯 ዲፓርትመንት: {student_dept}\n"
        f"🆔 ID: {user_id}"
    )
    await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=admin_caption, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("tg_"))
async def admin_toggle_selection(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ አድሚኑ ብቻ ነው!", show_alert=True)
        return
    parts = callback.data.split("_")
    target_user_id = int(parts[1])
    t_code = "_".join(parts[2:])
    subj, topic = TOPIC_KEYS.get(t_code, ("CS", t_code))
    full_key = f"{subj}_{topic}"

    admin_selections.setdefault(target_user_id, set())
    if full_key in admin_selections[target_user_id]:
        admin_selections[target_user_id].remove(full_key)
        await callback.answer(f"❌ {full_key} ተሰርዟል")
    else:
        admin_selections[target_user_id].add(full_key)
        await callback.answer(f"✅ {full_key} ተመርጧል")


@dp.callback_query(F.data.startswith("fapp_"))
async def admin_finalize_approve(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ አድሚኑ ብቻ ነው!", show_alert=True)
        return
    target_user_id = int(callback.data.split("_")[1])
    selected_keys = admin_selections.get(target_user_id, set())
    if not selected_keys:
        await callback.answer("⚠️ ቢያንስ አንድ ኮርስ ይምረጡ!", show_alert=True)
        return

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT paid_department FROM users WHERE user_id = ?", (target_user_id,))
        res = cur.fetchone()
        existing_depts = res[0].split(",") if res and res[0] else []
        combined_depts = set(filter(None, existing_depts)).union(selected_keys)
        new_paid_str = ",".join(sorted(combined_depts))
        cur.execute(
            """
            INSERT INTO users (user_id, payment_status, paid_department)
            VALUES (?, 'paid', ?)
            ON CONFLICT(user_id) DO UPDATE SET
                payment_status = 'paid',
                paid_department = excluded.paid_department
            """,
            (target_user_id, new_paid_str),
        )
        conn.commit()
    finally:
        conn.close()

    admin_selections.pop(target_user_id, None)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + f"\n\n✅ [APPROVED: {', '.join(sorted(selected_keys))}]",
        reply_markup=None,
    )
    await callback.answer("ክፍያው ጸድቋል!")
    try:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 ዋና ማውጫ", callback_data="back_menu"))
        await bot.send_message(
            target_user_id,
            "🎉 **እንኳን ደስ አለዎት!** አድሚኑ ክፍያዎን አረጋግጦታል (Approved)። በሚኒ አፕም ሆነ በቦቱ ሙሉ ጥያቄዎች ተከፍተውልዎታል! 🚀",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown",
        )
    except Exception as e:
        logging.error(f"Notify user error: {e}")


@dp.callback_query(F.data.startswith("rej_"))
async def admin_reject(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ አድሚኑ ብቻ ነው!", show_alert=True)
        return
    target_user_id = int(callback.data.split("_")[1])
    admin_selections.pop(target_user_id, None)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n❌ [REJECTED]", reply_markup=None
    )
    await callback.answer("ውድቅ ተደርጓል!")
    try:
        await bot.send_message(target_user_id, "❌ **ክፍያዎ ውድቅ ተደርጓል (Rejected)።**", parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Reject notify error: {e}")


@dp.callback_query(F.data.startswith("q_"))
async def start_specific_exam(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    raw = callback.data[2:]
    parts = raw.rsplit("_", 2)
    t_code = parts[0]
    offset_val = int(parts[1]) if len(parts) > 1 else 0
    current_score = int(parts[2]) if len(parts) > 2 else 0

    subj, topic = TOPIC_KEYS.get(t_code, ("CS", "2017 ጥር"))
    pay_key = f"{subj}_{topic}"

    conn = get_conn()
    try:
        is_paid_for_this = check_user_paid_for_topic(conn, user_id, subj, topic)
        if not is_paid_for_this and offset_val >= 3:
            await send_payment_prompt(callback.message, f"{subj} ({topic})", pay_key)
            return

        rows = get_questions_for_pair(conn, subj, topic)
    finally:
        conn.close()

    if offset_val < len(rows):
        q = rows[offset_val]
        q_id, q_text, opt_a, opt_b, opt_c, opt_d = q[0], q[1], q[2], q[3], q[4], q[5]

        builder = InlineKeyboardBuilder()
        for opt_letter, opt_val in [("A", opt_a), ("B", opt_b), ("C", opt_c), ("D", opt_d)]:
            builder.row(
                types.InlineKeyboardButton(
                    text=f"{opt_letter}) {opt_val}",
                    callback_data=f"a_{t_code}_{offset_val}_{q_id}_{current_score}_{opt_letter}",
                )
            )
        builder.row(
            types.InlineKeyboardButton(text="🔖 Bookmark", callback_data=f"bm_{q_id}"),
            types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"),
        )

        q_num_display = offset_val + 1
        rem_text = f" (ቀሪ ነጻ ጥያቄ: {max(0, 3 - offset_val)})" if not is_paid_for_this else " (VIP 🌟)"
        score_display = f" | ውጤት: {current_score}/{offset_val}" if offset_val > 0 else ""

        await callback.message.answer(
            f"📝 **Exam — Q{q_num_display}{score_display}{rem_text}:**\n\n{q_text}",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown",
        )
    else:
        percentage = int((current_score / offset_val) * 100) if offset_val > 0 else 0
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
        summary_text = (
            f"🎉 **እንኳን ደስ አለዎት!** በዚህ ምድብ ያሉትን ጥያቄዎች በሙሉ አጠናቀዋል።\n\n"
            f"📊 **የእርስዎ ውጤት:**\n"
            f"✅ ትክክለኛ መልሶች: **{current_score}/{offset_val}**\n"
            f"💯 መቶኛ: **{percentage}%**"
        )
        await callback.message.answer(summary_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("a_"))
async def check_answer(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    raw = callback.data[2:]
    parts = raw.rsplit("_", 4)
    t_code = parts[0]
    offset_val = int(parts[1])
    q_id = int(parts[2])
    current_score = int(parts[3])
    chosen_opt = parts[4]

    explanation = "ለዚህ ጥያቄ ማብራሪያ አልተሰጠም።"
    result_text = "⚠️ ጥያቄው አልተገኘም።"

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT correct_answer, explanation FROM questions WHERE id = ?", (q_id,))
        res = cur.fetchone()
        if res:
            correct, exp = res
            explanation = exp if exp else explanation
            cur.execute(
                """
                INSERT OR IGNORE INTO user_progress (user_id, total_attempted, correct_count, wrong_count)
                VALUES (?, 0, 0, 0)
                """,
                (user_id,),
            )
            if chosen_opt == correct:
                current_score += 1
                result_text = "✅ **Correct!**"
                cur.execute(
                    """
                    UPDATE user_progress
                    SET total_attempted = total_attempted + 1, correct_count = correct_count + 1
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
            else:
                result_text = f"❌ **Incorrect. Correct answer: {correct}**"
                cur.execute(
                    """
                    UPDATE user_progress
                    SET total_attempted = total_attempted + 1, wrong_count = wrong_count + 1
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
            conn.commit()
    finally:
        conn.close()

    next_offset = offset_val + 1
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="➡️ Next Question",
            callback_data=f"q_{t_code}_{next_offset}_{current_score}",
        )
    )
    builder.row(types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_menu"))
    await callback.message.answer(
        f"{result_text}\n\n💡 **Explanation:**\n{explanation}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data.startswith("bm_"))
async def handle_bookmark(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    q_id = int(callback.data.split("_")[1])
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO bookmarks (user_id, question_id) VALUES (?, ?)",
            (user_id, q_id),
        )
        conn.commit()
    finally:
        conn.close()
    await callback.answer("🔖 ጥያቄው ተቀምጧል (Bookmarked)!", show_alert=False)


async def main():
    load_all_exam_datasets()
    init_documents_table()
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("🌐 Flask Web Server started")
    logging.info("🚀 WanK Exam Bot is running live!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())