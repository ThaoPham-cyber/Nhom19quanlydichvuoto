from unittest.mock import MagicMock, patch
import gui_payments

def make_fake_payment_frame():
    frame = object.__new__(gui_payments.PaymentFrame)
    frame.load_invoices = MagicMock()
    frame.parent_app = MagicMock()
    return frame

def seed_invoice(db_connection, invoice_id, total_amount):
    cursor = db_connection.cursor()
    appt_id = invoice_id  # mỗi hóa đơn test dùng 1 appointment riêng, tránh trùng UNIQUE
    cursor.execute("DELETE FROM payments WHERE invoice_id=%s", (invoice_id,))
    cursor.execute("DELETE FROM invoices WHERE id=%s", (invoice_id,))
    cursor.execute("DELETE FROM appointments WHERE id=%s", (appt_id,))
    cursor.execute("""INSERT INTO appointments (id, customer_id, car_plate, appointment_date, status, progress_percent)
                       VALUES (%s, 1, '51F00000', NOW(), 'Cho xac nhan', 0)""", (appt_id,))
    cursor.execute("""INSERT INTO invoices (id, appointment_id, customer_id, total_amount, status, created_at)
                       VALUES (%s, %s, 1, %s, 'Chua thanh toan', NOW())""", (invoice_id, appt_id, total_amount))
    db_connection.commit()

@patch("gui_payments.messagebox")
def test_UTCID01_full_payment(mock_msgbox, db_connection):
    seed_invoice(db_connection, 901, 1_000_000)
    frame = make_fake_payment_frame()
    gui_payments.PaymentFrame.process_payment(
        frame, invoice_id=901, total_amount=1_000_000, paid_amount=0,
        payment_amount=1_000_000, modal=None, payment_method="Tiền mặt", note="")
    cursor = db_connection.cursor()
    cursor.execute("SELECT status FROM invoices WHERE id=901")
    assert cursor.fetchone()[0] == "Đã thanh toán"

@patch("gui_payments.messagebox")
def test_UTCID08_zero_amount_rejected(mock_msgbox, db_connection):
    seed_invoice(db_connection, 902, 1_000_000)
    frame = make_fake_payment_frame()
    gui_payments.PaymentFrame.process_payment(
        frame, invoice_id=902, total_amount=1_000_000, paid_amount=0,
        payment_amount=0, modal=None, payment_method="Tiền mặt", note="")
    mock_msgbox.showerror.assert_called()

@patch("gui_payments.messagebox")
def test_UTCID11_non_numeric_amount(mock_msgbox, db_connection):
    seed_invoice(db_connection, 903, 1_000_000)
    frame = make_fake_payment_frame()
    gui_payments.PaymentFrame.process_payment(
        frame, invoice_id=903, total_amount=1_000_000, paid_amount=0,
        payment_amount="abc", modal=None, payment_method="Tiền mặt", note="")
    args, _ = mock_msgbox.showerror.call_args
    print("Nội dung lỗi thực tế:", args[1])