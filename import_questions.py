import csv
import sqlite3
import pandas as pd

# 1. ዳታቤዙን ማገናኘት
DB_NAME = "brand_new_exam.db"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# 2. የጥያቄዎች ሰንጠረዥ (Table) መፍጠር (ከሌለ)
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
conn.close()

print("📂 የ CSV ፋይሎችን ወደ ዳታቤዝ መጫን ጀመረ...")

# 3. አራቱን ፋይሎች በ Pandas በመጠቀም በቅደም ተከተል መጫን
conn = sqlite3.connect(DB_NAME)

files_to_import = [
    ("CS_2018_Tir_100_Questions.csv", "CS", "ጥር"),
    ("CS_2018_Sane_100_Questions.csv", "CS", "ሰኔ"),
    ("IT_2018_Tir_100_Questions.csv", "IT", "ጥር"),
    ("IT_2018_Sane_100_Questions.csv", "IT", "ሰኔ")
]

for file_name, subj, year in files_to_import:
    try:
        df = pd.read_csv(file_name)
        df['subject'] = subj
        df['exam_year'] = year
        df.to_sql("questions", conn, if_exists="append", index=False)
        print(f"✅ {file_name} (Subject: {subj}, Year: {year}) በተሳካ ሁኔታ ተጫኗል!")
    except Exception as e:
        print(f"❌ ስህተት በ {file_name} ላይ: {e}")

conn.commit()
conn.close()

# 4. በ csv.DictReader በመጠቀም ተጨማሪ ማረጋገጫ ወይም ሌላ ፋይል መጫን ከፈለጉ
count = 0
try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    with open('CS_2018_Tir_100_Questions.csv', mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        # ጃምፕ እንዳይበዛ ወይም በድጋሚ እንዳይገባ በልዩ ሁኔታ መመልከት ይቻላል
        # (ለአሁኑ ޕንዳስ በቂ ስራ ስለሰራ ይህንን እንደ ተጨማሪ ምሳሌ ማየት ይችላሉ)
    conn.close()
except Exception as e:
    pass

print("🎉 ሁሉም ፋይሎች ወደ brand_new_exam.db በሰላም ተጭነዋል!")