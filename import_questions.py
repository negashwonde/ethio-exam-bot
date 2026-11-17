import os
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# WANK EXAM BOT - SAFE DATABASE IMPORTER
# ==========================================

DB_NAME = "brand_new_exam.db"

# ==========================================
# 1. DATABASE BACKUP
# ==========================================
def backup_database():
    if not os.path.exists(DB_NAME):
        print("New database. No backup needed.")
        return

    backup_name = f"brand_new_exam_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    source = sqlite3.connect(DB_NAME)
    destination = sqlite3.connect(backup_name)

    try:
        source.backup(destination)
        print(f"Backup created: {backup_name}")
    finally:
        destination.close()
        source.close()

# ==========================================
# 2. CREATE DATABASE TABLES
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    try:
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
        print("Database tables are ready.")
    finally:
        conn.close()

# ==========================================
# 3. CSV FILES (7ቱም የፍሬሽማን እና የ CS/IT ፋይሎች)
# ==========================================
FILES_TO_IMPORT = [
    ("CS_2017_Tir_100_Unique_Final.csv", "CS", "2017 ጥር"),
    ("CS_2017_Sane_100_Unique_Final.csv", "CS", "2017 ሰኔ"),
    ("IT_2017_Tir_100_Unique_Final.csv", "IT", "2017 ጥር"),
    ("IT_2017_Sane_100_Unique_Final.csv", "IT", "2017 ሰኔ"),
    ("CS_2018_Tir_100_Questions_Distinct.csv", "CS", "2018 ጥር"),
    ("CS_2018_Sane_100_Questions_Distinct.csv", "CS", "2018 ሰኔ"),
    ("IT_2018_Tir_100_Questions_Distinct.csv", "IT", "2018 ጥር"),
    ("IT_2018_Sane_100_Questions_Distinct.csv", "IT", "2018 ሰኔ"),
    ("Freshman_Psychology_Complete_Master_85Qs.csv", "Freshman", "Psychology"),
    ("Geography_Ethiopia_Horn_100_Balanced_Answers.csv", "Freshman", "Geography"),
    ("Logic_and_Critical_Thinking_100_Balanced.csv", "Freshman", "Logic"),
    ("Communicative_English_Mid_Exam_100_Questions_3.csv", "Freshman", "English"),
    ("General_Physics_Ch1_Ch2_100_Questions_3.csv", "Freshman", "Physics"),
    ("Inclusiveness_Ch1_Ch2_100_Mid_Exam_Questions_3.csv", "Freshman", "Inclusiveness"),
    ("Math_Natural_Sciences_Ch1_Ch2_MidExam_100Q_3.csv", "Freshman", "Math")
]

# ==========================================
# 4. SAFE CSV IMPORT
# ==========================================
def load_all_exam_datasets():
    print("\nStarting SAFE CSV Import...")

    required_columns = [
        "question_text", "option_a", "option_b",
        "option_c", "option_d", "correct_answer", "explanation"
    ]

    prepared_files = []

    for file_name, subject, exam_year in FILES_TO_IMPORT:
        if not os.path.exists(file_name):
            print(f"Missing file: {file_name}")
            continue

        try:
            try:
                df = pd.read_csv(file_name, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(file_name, encoding="latin1")

            df.columns = [str(column).strip().lower() for column in df.columns]

            if 'question' in df.columns and 'question_text' not in df.columns:
                df = df.rename(columns={'question': 'question_text'})
            if 'correct_option' in df.columns and 'correct_answer' not in df.columns:
                df = df.rename(columns={'correct_option': 'correct_answer'})

            missing = [column for column in required_columns if column not in df.columns]
            if missing:
                print(f"⚠️ Warning: {file_name} missing columns {missing}, skipping.")
                continue

            df = df[required_columns].fillna("")
            records = []

            for _, row in df.iterrows():
                q_text = str(row["question_text"]).strip()
                if not q_text:
                    continue

                records.append((
                    subject,
                    exam_year,
                    q_text,
                    str(row["option_a"]).strip(),
                    str(row["option_b"]).strip(),
                    str(row["option_c"]).strip(),
                    str(row["option_d"]).strip(),
                    str(row["correct_answer"]).strip().upper(),
                    str(row["explanation"]).strip()
                ))

            prepared_files.append((file_name, records))
            print(f"Validated {file_name}: {len(records)} questions")

        except Exception as error:
            print(f"CSV validation failed for {file_name}: {error}")

    if not prepared_files:
        print("No CSV files processed.")
        return

    conn = sqlite3.connect(DB_NAME)
    inserted_total = 0
    skipped_total = 0

    try:
        conn.execute("BEGIN")
        for file_name, records in prepared_files:
            file_inserted = 0
            for record in records:
                cursor = conn.execute("""
                    INSERT INTO questions (
                        subject, exam_year, question_text, 
                        option_a, option_b, option_c, option_d, 
                        correct_answer, explanation
                    )
                    SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM questions
                        WHERE subject = ? AND exam_year = ? AND question_text = ?
                    )
                """, record + (record[0], record[1], record[2]))

                if cursor.rowcount:
                    inserted_total += 1
                    file_inserted += 1
                else:
                    skipped_total += 1

            print(f"{file_name}: {file_inserted} new questions imported.")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("\nSAFE IMPORT COMPLETED!")
    print(f"New questions: {inserted_total}")
    print(f"Existing questions skipped: {skipped_total}")

# ==========================================
# 5. RUN SCRIPT
# ==========================================
if __name__ == "__main__":
    print("WANK EXAM BOT - DATABASE IMPORT SCRIPT")
    backup_database()
    init_db()
    load_all_exam_datasets()
    print("\nAll database tasks finished successfully.")