import sys
import os

STAFF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "staff")
sys.path.insert(0, STAFF_DIR)

import pytest
import database
import mysql.connector

TEST_DB_CONFIG = dict(host="127.0.0.1", user="root", password="",
                       port=3308, database="autocare_test")


@pytest.fixture(scope="session", autouse=True)
def seed_base_data():
    """Tạo sẵn dữ liệu gốc (customer=1, service=1, car, appointment=1) một lần cho cả phiên test."""
    conn = mysql.connector.connect(**TEST_DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""INSERT IGNORE INTO customers (id, full_name, phone, email, visit_count)
                       VALUES (1, 'Khach test', '0900000000', '', 1)""")
    cursor.execute("""INSERT IGNORE INTO services (id, service_name, price)
                       VALUES (1, 'Dich vu test', 100000)""")
    cursor.execute("""INSERT IGNORE INTO cars (plate_number, brand, model, year, customer_id)
                       VALUES ('51F00000', 'Test', 'Test', 2020, 1)""")
    cursor.execute("""INSERT IGNORE INTO appointments (id, customer_id, car_plate, appointment_date, status, progress_percent)
                       VALUES (1, 1, '51F00000', NOW(), 'Cho xac nhan', 0)""")
    conn.commit()
    conn.close()
    yield


@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    def fake_connect_db():
        return mysql.connector.connect(**TEST_DB_CONFIG)

    monkeypatch.setattr("database.connect_db", fake_connect_db)
    try:
        import gui_appointments
        monkeypatch.setattr("gui_appointments.connect_db", fake_connect_db)
    except ImportError:
        pass
    try:
        import gui_payments
        monkeypatch.setattr("gui_payments.connect_db", fake_connect_db)
    except ImportError:
        pass
    try:
        import gui_inventory
        monkeypatch.setattr("gui_inventory.connect_db", fake_connect_db)
    except ImportError:
        pass


@pytest.fixture
def db_connection():
    conn = database.connect_db()
    yield conn
    conn.rollback()
    conn.close()