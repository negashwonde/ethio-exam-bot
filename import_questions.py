import pandas as pd
import sqlite3

DB_NAME = "brand_new_exam.db"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# ሰንጠረዡ መኖሩን ማረጋገጥ
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

# አሮጌዎቹን ጥያቄዎች ማጽዳት
cursor.execute("DELETE FROM questions")
conn.commit()
conn.close()

print("📂 የጥር እና የሰኔ ወር የተለዩ (Distinct) 100-100 ጥያቄዎችን መጫን ጀመረ...")

conn = sqlite3.connect(DB_NAME)

files_to_import = [
    ("CS_2018_Tir_100_Questions_Distinct.csv", "CS", "ጥር"),
    ("CS_2018_Sane_100_Questions_Distinct.csv", "CS", "ሰኔ"),
    ("IT_2018_Tir_100_Questions_Distinct.csv", "IT", "ጥር"),
    ("IT_2018_Sane_100_Questions_Distinct.csv", "IT", "ሰኔ")
]

for file_name, subj, year in files_to_import:
    try:
        df = pd.read_csv(file_name)
        df['subject'] = subj
        df['exam_year'] = year
        df.to_sql("questions", conn, if_exists="append", index=False)
        print(f"✅ {file_name} (Subject: {subj}, Year: {year}) በትክክል ተጫኗል!")
    except Exception as e:
        print(f"❌ ስህተት በ {file_name} ላይ: {e}")

conn.commit()
conn.close()

print("🎉 የጥር እና ሰኔ ጥያቄዎች ሙሉ በሙሉ ተለይተው ተጭነዋል!")