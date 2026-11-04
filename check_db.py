import sqlite3

conn = sqlite3.connect('brand_new_exam.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM questions')
count = cursor.fetchone()[0]
print(f'✅ በዳታቤዙ ውስጥ ያሉ ጠቅላላ ጥያቄዎች ብዛት: {count}')
conn.close()
import sqlite3

conn = sqlite3.connect('brand_new_exam.db')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT subject, exam_year FROM questions LIMIT 5')
print(cursor.fetchall())
conn.close()