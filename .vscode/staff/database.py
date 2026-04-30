from tkinter import FALSE

import mysql.connector
def get_products_for_service(service_id):
    """Lấy danh sách vật tư cần cho dịch vụ"""
    db = connect_db()
    if not db:
        return []
    
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id, p.product_name, sp.quantity_needed, p.stock_quantity, p.price
        FROM service_products sp
        JOIN inventory p ON sp.product_id = p.id
        WHERE sp.service_id = %s
    """, (service_id,))
    products = cursor.fetchall()
    db.close()
    return products

def deduct_inventory(product_id, quantity):
    """Trừ tồn kho khi sử dụng vật tư"""
    db = connect_db()
    if not db:
        return False
    
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE inventory SET stock_quantity = stock_quantity - %s WHERE id = %s", (quantity, product_id))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Lỗi trừ kho: {e}")
        return False
    finally:
        db.close()
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
    
    
    
    