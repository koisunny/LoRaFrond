import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",   # hoặc localhost
        user="appuser",
        password="",        # đúng như lúc bạn connect
        database="qlsinhvien",
        port=3306,          # 👈 QUAN TRỌNG
        charset="utf8mb4"
    )
