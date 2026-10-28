import csv
import sqlite3

# 1. ዳታቤዙን ማገናኘት
conn = sqlite3.connect('brand_new_exam.db')
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

# 3. ከ CSV ፋይል ጥያቄዎችን አንብቦ ወደ ዳታቤዝ ማስገባት
count = 0
try:
  with open(
      'CS_2018_Tir_100_Questions.csv', mode='r', encoding='utf-8'
  ) as infile:
    reader = csv.DictReader(infile)
    for row in reader:
      cursor.execute(
          """
                INSERT INTO questions (subject, exam_year, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
          (
              row.get('subject'),
              row.get('exam_year'),
              row.get('question_text'),
              row.get('option_a'),
              row.get('option_b'),
              row.get('option_c'),
              row.get('option_d'),
              row.get('correct_answer'),
              row.get('explanation'),
          ),
      )
      count += 1
  conn.commit()
  print(f'✅ {count} ጥያቄዎች በትክክል ወደ ዳታቤዝ ተጭነዋል!')
except Exception as e:
  print(f'❌ ስህተት ተፈጥሯል: {e}')
finally:
  conn.close()