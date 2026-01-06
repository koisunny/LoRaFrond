import os
from flask import Flask, render_template
import mysql.connector

app = Flask(
    __name__,
    template_folder="views",
    static_folder="static"
)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("127.0.0.1"),
        user=os.getenv("root    "),
        password=os.getenv("2407"),
        database=os.getenv("qlsinhvien"),
        port = 3306,
        charset="utf8"
    )

@app.route("/")
def index():
    return render_template("middle.html")

@app.route("/diemdanh")
def diemdanh():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT ma_sv, ten_sv, trang_thai
        FROM sinh_vien
        WHERE ma_lop = '22DRTA1'
        ORDER BY ten_sv
    """)

    sinh_vien = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("diemdanh.html", sinh_vien=sinh_vien)
