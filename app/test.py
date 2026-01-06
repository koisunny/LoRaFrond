import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="appuser",
    password="",
    database="qlsinhvien",
    port=3306
)

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM sinh_vien")
print(cur.fetchone())

cur.close()
conn.close()
