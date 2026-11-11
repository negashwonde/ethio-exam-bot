import os
import sqlite3
import pandas as pd

DB_NAME = "brand_new_exam.db"


def load_all_exam_datasets():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. ሠንጠረዡ መኖሩን ማረጋገጥ
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
    conn.commit()

    # 2. አሮጌዎቹን ጥያቄዎች ማጽዳት (Clean/Reset)
    cursor.execute("DELETE FROM questions")
    conn.commit()
    conn.close()

    print(
        "📂 የ CS, IT እና የፍሬሽማን ጥያቄዎችን በንጹህ ኢንኮዲንግ መጫን ጀመረ..."
    )

    conn = sqlite3.connect(DB_NAME)

    # ሊጫኑ የሚገባቸው ሁሉም ፋይሎች ዝርዝር (የ CS, IT እና የፍሬሽማን ፋይሎች)
    files_to_import = [
        # የ 2017 ዓ.ም Unique Final ፋይሎች
        ("CS_2017_Tir_100_Unique_Final.csv", "CS", "ጥር"),
        ("CS_2017_Sane_100_Unique_Final.csv", "CS", "ሰኔ"),
        ("IT_2017_Tir_100_Unique_Final.csv", "IT", "ጥር"),
        ("IT_2017_Sane_100_Unique_Final.csv", "IT", "ሰኔ"),
        # የ 2018 ዓ.ም ፋይሎች
        ("CS_2018_Tir_100_Questions_Distinct.csv", "CS", "ጥር"),
        ("CS_2018_Sane_100_Questions_Distinct.csv", "CS", "ሰኔ"),
        ("IT_2018_Tir_100_Questions_Distinct.csv", "IT", "ጥር"),
        ("IT_2018_Sane_100_Questions_Distinct.csv", "IT", "ሰኔ"),
        # የፍሬሽማን ናቹራል ሳይንስ ኮርሶች (Freshman Natural Science Datasets)
        ("Freshman_Psychology_Complete_Master_85Qs.csv", "Freshman", "Psychology"),
        ("Geography_Ethiopia_Horn_100_Balanced_Answers.csv", "Freshman", "Geography"),
        ("Logic_and_Critical_Thinking_100_Balanced.csv", "Freshman", "Logic"),
    ]

    for file_name, subj, year in files_to_import:
        if os.path.exists(file_name):
            try:
                try:
                    df = pd.read_csv(file_name, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_name, encoding='latin1')

                df["subject"] = subj
                df["exam_year"] = year
                df.to_sql("questions", conn, if_exists="append", index=False)
                print(f"✅ {file_name} (Subject: {subj}, Year: {year}) በትክክል ተጫኗል!")
            except Exception as e:
                print(f"❌ ስህተት በ {file_name} ላይ: {e}")
        else:
            print(
                f"⚠️ ማስጠንቀቂያ: {file_name} በፎልደሩ ውስጥ አልተገኘም (ዘለለ)."
            )

    conn.commit()
    conn.close()
    print("🎉 ሁሉም የ CS, IT እና የፍሬሽማን የፈተና ጥያቄዎች ተጭነዋል!")


if __name__ == "__main__":
    load_all_exam_datasets()