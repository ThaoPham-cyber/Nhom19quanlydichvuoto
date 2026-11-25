import database

def seed_product(db_connection, product_id, stock, min_stock=5):
    cursor = db_connection.cursor()
    code = f"TEST{product_id}"
    cursor.execute("DELETE FROM inventory WHERE id=%s OR product_code=%s", (product_id, code))
    cursor.execute("""INSERT INTO inventory
        (id, product_code, product_name, category, brand, stock_quantity, min_stock, unit, price)
        VALUES (%s, %s, 'Dau test', 'Phu tung', 'Castrol', %s, %s, 'Lit', 100000)""",
        (product_id, code, stock, min_stock))
    db_connection.commit()

def get_stock(db_connection, product_id):
    cursor = db_connection.cursor()
    cursor.execute("SELECT stock_quantity FROM inventory WHERE id=%s", (product_id,))
    return cursor.fetchone()[0]

def test_UTCID01_deduct_valid(db_connection):
    seed_product(db_connection, 901, stock=50)
    result = database.deduct_inventory(901, 5)
    assert result is True
    assert get_stock(db_connection, 901) == 45

def test_UTCID06_over_stock_should_allow_negative(db_connection):
    seed_product(db_connection, 902, stock=10)
    result = database.deduct_inventory(902, 11)
    assert result is True
    assert get_stock(db_connection, 902) == -1

def test_UTCID08_negative_quantity_should_be_rejected(db_connection):
    seed_product(db_connection, 903, stock=10)
    result = database.deduct_inventory(903, -5)
    assert result is False

def test_UTCID09_nonexistent_product_should_return_false(db_connection):
    result = database.deduct_inventory(999999, 1)
    assert result is False