import sqlite3

# ዳታቤዙን ማገናኘት
conn = sqlite3.connect('brand_new_exam.db')
cursor = conn.cursor()

# ጠቅላላ የጥያቄዎችን ብዛት ማየት
cursor.execute('SELECT COUNT(*) FROM questions')
count = cursor.fetchone()[0]
print(f'✅ በዳታቤዙ ውስጥ ያሉ ጠቅላላ ጥያቄዎች ብዛት: {count}')

# የመጀመሪያዎቹን 3 ጥያቄዎች ማየት
cursor.execute('SELECT id, question_text FROM questions LIMIT 3')
rows = cursor.fetchall()
print('\nየተጫኑ ጥያቄዎች ናሙና:')
for row in rows:
  print(f'ID: {row[0]} - {row[1]}')

conn.close()