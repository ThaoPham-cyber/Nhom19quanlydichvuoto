from unittest.mock import MagicMock, patch
import gui_appointments

def make_fake_frame(name="Lê Văn C", phone="0901234567", email="", plate="51F12345",
                     brand="", model="", year_str="", date_str="2026-10-15",
                     time_str="09:00", services=(1,)):
    frame = object.__new__(gui_appointments.AppointmentFrame)
    frame.ent_name  = MagicMock(**{"get.return_value": name})
    frame.ent_phone = MagicMock(**{"get.return_value": phone})
    frame.ent_email = MagicMock(**{"get.return_value": email})
    frame.ent_plate = MagicMock(**{"get.return_value": plate})
    frame.ent_brand = MagicMock(**{"get.return_value": brand})
    frame.ent_model = MagicMock(**{"get.return_value": model})
    frame.ent_year  = MagicMock(**{"get.return_value": year_str})
    frame.date_pick = MagicMock(**{"get.return_value": date_str})
    frame.time_ent  = MagicMock(**{"get.return_value": time_str})
    frame.svc_vars = {sid: MagicMock(**{"get.return_value": True}) for sid in services}
    frame.modal_window = MagicMock()
    frame.load = MagicMock()
    return frame

@patch("gui_appointments.messagebox")
def test_UTCID12_empty_name_rejected(mock_msgbox):
    frame = make_fake_frame(name="   ")
    gui_appointments.AppointmentFrame.save_appointment(frame)
    mock_msgbox.showerror.assert_called_with(
        "Lỗi", "Vui lòng nhập đầy đủ thông tin bắt buộc!")

@patch("gui_appointments.messagebox")
def test_UTCID13_no_service_selected_rejected(mock_msgbox):
    frame = make_fake_frame(services=())
    gui_appointments.AppointmentFrame.save_appointment(frame)
    mock_msgbox.showerror.assert_called_with(
        "Lỗi", "Vui lòng chọn ít nhất 1 dịch vụ!")

@patch("gui_appointments.messagebox")
def test_UTCID07_long_phone_should_be_rejected(mock_msgbox, db_connection):
    phone = "9" * 20
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM appointments WHERE customer_id IN (SELECT id FROM customers WHERE phone LIKE %s)", (phone[:15] + "%",))
    cursor.execute("DELETE FROM customers WHERE phone LIKE %s", (phone[:15] + "%",))
    db_connection.commit()
    frame = make_fake_frame(phone=phone, plate="51F99999")
    gui_appointments.AppointmentFrame.save_appointment(frame)
    mock_msgbox.showerror.assert_any_call("Lỗi", "Số điện thoại không hợp lệ!")