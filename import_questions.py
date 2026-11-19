import logging
import os
import re
import sqlite3
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DB_PATH = os.environ.get("DB_PATH", "brand_new_exam.db")
DATA_DIR = os.environ.get("EXAM_DATA_DIR", ".")

FILES_TO_IMPORT = [
    # Computer Science Exit Exams
    ("CS_2017_Tir_100_Unique_Final.csv", "CS", "2017 ጥር"),
    ("CS_2017_Sane_100_Unique_Final.csv", "CS", "2017 ሰኔ"),
    ("CS_2018_Tir_100_Questions_Distinct.csv", "CS", "2018 ጥር"),
    ("CS_2018_Sane_100_Questions_Distinct.csv", "CS", "2018 ሰኔ"),

    # Information Technology Exit Exams
    ("IT_2017_Tir_100_Unique_Final.csv", "IT", "2017 ጥር"),
    ("IT_2017_Sane_100_Unique_Final.csv", "IT", "2017 ሰኔ"),
    ("IT_2018_Tir_100_Questions_Distinct.csv", "IT", "2018 ጥር"),
    ("IT_2018_Sane_100_Questions_Distinct.csv", "IT", "2018 ሰኔ"),

    # Freshman Program (Natural Science)
    ("Freshman_Psychology_Complete_Master_85Qs.csv", "Freshman", "Psychology"),
    ("Geography_Ethiopia_Horn_100_Balanced_Answers.csv", "Freshman", "Geography"),
    ("Logic_and_Critical_Thinking_100_Balanced.csv", "Freshman", "Logic"),
    ("Communicative_English_Mid_Exam_100_Questions.csv", "Freshman", "English"),
    ("General_Physics_Ch1_Ch2_100_Questions.csv", "Freshman", "Physics"),
    ("Inclusiveness_Ch1_Ch2_100_Mid_Exam_Questions.csv", "Freshman", "Inclusiveness"),
    ("Math_Natural_Sciences_Ch1_Ch2_MidExam_100Q.csv", "Freshman", "Math"),

    # Freshman Program (Social Science)
    ("freshman_direct_download_Anthropology_100_Questions.csv", "Freshman_Social", "Anthropology"),
    ("freshman_direct_download_Geography_of_Ethiopia_100_Questions.csv", "Freshman_Social", "Geography"),
    ("freshman_direct_download_History_of_Ethiopia_and_the_Horn_100_Questions.csv", "Freshman_Social", "History"),
    ("freshman_direct_download_Logic_and_Critical_Thinking_100_Questions.csv", "Freshman_Social", "Logic"),
    ("freshman_direct_download_Civics_and_Ethical_Studies_100_Questions.csv", "Freshman_Social", "Civics"),
    ("freshman_direct_download_Global_Trends_100_Questions.csv", "Freshman_Social", "Global_Trends"),
]


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def normalize_answer(raw_ans: str) -> str:
    txt = str(raw_ans or "").strip().upper()
    match = re.search(r"\b([ABCD])\b", txt)
    if match:
        return match.group(1)
    if txt and txt[0] in ("A", "B", "C", "D"):
        return txt[0]
    return "A"


def backup_database(keep_last: int = 5):
    if not os.path.exists(DB_PATH):
        return
    os.makedirs("backups", exist_ok=True)
    backup_name = os.path.join(
        "backups", f"brand_new_exam_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    )
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(backup_name)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    all_backups = sorted(
        [os.path.join("backups", f) for f in os.listdir("backups") if f.endswith(".db")],
        key=os.path.getmtime,
        reverse=True,
    )
    for old_file in all_backups[keep_last:]:
        try:
            os.remove(old_file)
        except OSError:
            pass


def init_db():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                exam_year TEXT NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT DEFAULT ''
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                department TEXT DEFAULT 'CS',
                lang TEXT DEFAULT 'am',
                free_questions_used INTEGER DEFAULT 0,
                payment_status TEXT DEFAULT 'free',
                paid_department TEXT DEFAULT ''
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                user_id INTEGER,
                question_id INTEGER,
                PRIMARY KEY(user_id, question_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id INTEGER PRIMARY KEY,
                total_attempted INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_questions_unique
            ON questions(subject, exam_year, question_text)
        """)
        conn.commit()
    finally:
        conn.close()


def _read_csv_flexible(full_path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
        try:
            return pd.read_csv(full_path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(full_path, encoding="utf-8", errors="replace")


def load_all_exam_datasets(custom_files=None):
    """
    ነባር ጥያቄዎችን ሳያጠፋ አዳዲስ ጥያቄዎችን ብቻ (duplicate ያልሆኑትን) ይጨምራል።
    """
    init_db()
    required_cols = [
        "question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer", "explanation"
    ]
    targets = list(FILES_TO_IMPORT)
    if custom_files:
        targets.extend(custom_files)

    conn = get_conn()
    total_added = 0
    try:
        for file_name, subject, exam_year in targets:
            full_path = file_name if os.path.isabs(file_name) else os.path.join(DATA_DIR, file_name)
            if not os.path.exists(full_path):
                logging.warning(f"CSV file not found (skipped): {full_path}")
                continue

            try:
                df = _read_csv_flexible(full_path)
                df.columns = [str(c).strip().lower() for c in df.columns]

                rename_map = {}
                if "question" in df.columns and "question_text" not in df.columns:
                    rename_map["question"] = "question_text"
                if "correct_option" in df.columns and "correct_answer" not in df.columns:
                    rename_map["correct_option"] = "correct_answer"
                if "answer" in df.columns and "correct_answer" not in df.columns:
                    rename_map["answer"] = "correct_answer"
                if rename_map:
                    df = df.rename(columns=rename_map)

                if "explanation" not in df.columns:
                    df["explanation"] = ""

                missing = [c for c in required_cols if c not in df.columns]
                if missing:
                    logging.error(f"Missing columns {missing} in {file_name}. Found: {list(df.columns)}")
                    continue

                df = df[required_cols].fillna("")
                added_for_file = 0

                conn.execute("BEGIN")
                for _, row in df.iterrows():
                    q_text = str(row["question_text"]).strip()
                    if not q_text:
                        continue
                    cur = conn.execute(
                        """
                        INSERT OR IGNORE INTO questions (
                            subject, exam_year, question_text,
                            option_a, option_b, option_c, option_d,
                            correct_answer, explanation
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            subject,
                            exam_year,
                            q_text,
                            str(row["option_a"]).strip(),
                            str(row["option_b"]).strip(),
                            str(row["option_c"]).strip(),
                            str(row["option_d"]).strip(),
                            normalize_answer(row["correct_answer"]),
                            str(row["explanation"]).strip(),
                        ),
                    )
                    if cur.rowcount > 0:
                        added_for_file += 1

                conn.commit()
                total_added += added_for_file
                logging.info(f"[{subject} | {exam_year}] {file_name}: +{added_for_file} new questions added.")
            except Exception as e:
                conn.rollback()
                logging.error(f"Failed importing {file_name}: {e}")

        summary = conn.execute(
            "SELECT subject, exam_year, COUNT(*) FROM questions GROUP BY subject, exam_year ORDER BY subject, exam_year"
        ).fetchall()
        logging.info(f"Import finished. Total newly added in this run: {total_added}")
        for s, y, cnt in summary:
            logging.info(f"  -> {s} / {y}: {cnt} questions in DB")
    finally:
        conn.close()


if __name__ == "__main__":
    backup_database()
    load_all_exam_datasets()