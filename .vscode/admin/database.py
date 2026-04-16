import mysql.connector

def connect_db():
    try:
        db = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="", # Điền password nếu bạn đã đặt
            port=3308,   # BẮT BUỘC ĐỔI THÀNH 3308 theo file config của bạn
            database="autocare_manager" # Tên database bạn đã tạo
        )
        return db
    except Exception as e:
        print(f"Lỗi kết nối: {e}")
        return None