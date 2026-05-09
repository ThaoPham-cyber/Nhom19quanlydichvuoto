import mysql.connector

def connect_db():
    try:
        db = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            port=3308,   
            database="autocare_manager" 
        )
        return db
    except Exception as e:
        print(f"Lỗi kết nối: {e}")
        return None