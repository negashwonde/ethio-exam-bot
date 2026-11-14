
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

    backup_name = (
        f"brand_new_exam_backup_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    )

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
# 3. CSV FILES
# ==========================================

FILES_TO_IMPORT = [

    ("CS_2017_Tir_100_Unique_Final.csv",
     "CS", "2017 ጥር"),

    ("CS_2017_Sane_100_Unique_Final.csv",
     "CS", "2017 ሰኔ"),

    ("IT_2017_Tir_100_Unique_Final.csv",
     "IT", "2017 ጥር"),

    ("IT_2017_Sane_100_Unique_Final.csv",
     "IT", "2017 ሰኔ"),

    ("CS_2018_Tir_100_Questions_Distinct.csv",
     "CS", "2018 ጥር"),

    ("CS_2018_Sane_100_Questions_Distinct.csv",
     "CS", "2018 ሰኔ"),

    ("IT_2018_Tir_100_Questions_Distinct.csv",
     "IT", "2018 ጥር"),

    ("IT_2018_Sane_100_Questions_Distinct.csv",
     "IT", "2018 ሰኔ"),

    ("Freshman_Psychology_Complete_Master_85Qs.csv",
     "Freshman", "Psychology"),

    ("Geography_Ethiopia_Horn_100_Balanced_Answers.csv",
     "Freshman", "Geography"),

    ("Logic_and_Critical_Thinking_100_Balanced.csv",
     "Freshman", "Logic"),
]


# ==========================================
# 4. SAFE CSV IMPORT
# ==========================================

def load_all_exam_datasets():

    print("\nStarting SAFE CSV Import...")

    required_columns = [
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "explanation"
    ]

    prepared_files = []

    # Read and validate CSV files first.
    for file_name, subject, exam_year in FILES_TO_IMPORT:

        if not os.path.exists(file_name):
            print(f"Missing file: {file_name}")
            continue

        try:

            try:
                df = pd.read_csv(
                    file_name,
                    encoding="utf-8-sig"
                )

            except UnicodeDecodeError:
                df = pd.read_csv(
                    file_name,
                    encoding="latin1"
                )

            # Normalize column names.
            df.columns = [
                str(column).strip().lower()
                for column in df.columns
            ]

            missing = [
                column for column in required_columns
                if column not in df.columns
            ]

            if missing:
                raise ValueError(
                    f"Missing CSV columns: {missing}"
                )

            df = df[required_columns].fillna("")

            records = []

            for _, row in df.iterrows():

                question_text = str(
                    row["question_text"]
                ).strip()

                if not question_text:
                    continue

                records.append((
                    subject,
                    exam_year,
                    question_text,
                    str(row["option_a"]).strip(),
                    str(row["option_b"]).strip(),
                    str(row["option_c"]).strip(),
                    str(row["option_d"]).strip(),
                    str(row["correct_answer"]).strip().upper(),
                    str(row["explanation"]).strip()
                ))

            prepared_files.append(
                (file_name, records)
            )

            print(
                f"Validated {file_name}: "
                f"{len(records)} questions"
            )

        except Exception as error:

            print(f"CSV validation failed: {file_name}")

            raise RuntimeError(
                "Import stopped. Database questions were not changed."
            ) from error

    if not prepared_files:

        print("No CSV files found.")
        print("Existing questions preserved.")
        return

    # Connect to database.
    conn = sqlite3.connect(DB_NAME)

    inserted_total = 0
    skipped_total = 0

    try:

        # Start one transaction for all imports.
        conn.execute("BEGIN")

        for file_name, records in prepared_files:

            file_inserted = 0

            for record in records:

                cursor = conn.execute("""
                    INSERT INTO questions (
                        subject,
                        exam_year,
                        question_text,
                        option_a,
                        option_b,
                        option_c,
                        option_d,
                        correct_answer,
                        explanation
                    )
                    SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM questions
                        WHERE subject = ?
                        AND exam_year = ?
                        AND question_text = ?
                    )
                """, record + (
                    record[0],
                    record[1],
                    record[2]
                ))

                if cursor.rowcount:

                    inserted_total += 1
                    file_inserted += 1

                else:

                    skipped_total += 1

            print(
                f"{file_name}: "
                f"{file_inserted} new questions imported."
            )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()

    print("\nSAFE IMPORT COMPLETED!")
    print(f"New questions: {inserted_total}")
    print(f"Existing questions skipped: {skipped_total}")
    print("Existing database records preserved.")


# ==========================================
# 5. RUN IMPORT SCRIPT
# ==========================================

if __name__ == "__main__":

    print("WANK EXAM BOT - DATABASE IMPORT")

    # Backup existing database first.
    backup_database()

    # Create required tables.
    init_db()

    # Import CSV questions.
    load_all_exam_datasets()

    print("\nAll tasks finished.")
