import customtkinter as ctk
from database import connect_db
from tkinter import messagebox
from datetime import datetime

class AppointmentFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=35, pady=(25, 15))
        
        ctk.CTkLabel(header, text="Lịch hẹn", font=("Arial", 28, "bold"), text_color="#0f172a").pack(side="left")
        
        ctk.CTkButton(header, text="+ Tạo lịch hẹn", fg_color="#2563eb", hover_color="#1d4ed8",
                      font=("Arial", 13, "bold"), height=40, corner_radius=8,
                      command=self.open_appointment_modal).pack(side="right")

        # --- SEARCH ---
        filter_f = ctk.CTkFrame(self, fg_color="transparent")
        filter_f.grid(row=1, column=0, sticky="ew", padx=35, pady=(0, 20))
        self.ent_search = ctk.CTkEntry(filter_f, placeholder_text="🔍 Tìm kiếm lịch hẹn...", 
                                       height=45, fg_color="white", border_color="#e2e8f0")
        self.ent_search.pack(side="left", fill="x", expand=True)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_appointments())

        # --- LIST AREA ---
        self.scroll_list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_list.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
        
        self.load_appointments()

    def load_appointments(self):
        """Tải và hiển thị danh sách lịch hẹn ngay lập tức"""
        for w in self.scroll_list.winfo_children(): w.destroy()
        db = connect_db()
        if db:
            try:
                cursor = db.cursor()
                search = f"%{self.ent_search.get()}%"
                # Join với bảng customers và services để lấy thông tin đầy đủ
                query = """
                    SELECT a.id, c.full_name, a.car_plate, s.service_name, a.appointment_date, a.status
                    FROM appointments a
                    JOIN customers c ON a.customer_id = c.id
                    LEFT JOIN services s ON a.service_id = s.id
                    WHERE c.full_name LIKE %s OR a.car_plate LIKE %s
                    ORDER BY a.appointment_date DESC
                """
                cursor.execute(query, (search, search))
                rows = cursor.fetchall()
                for row in rows:
                    self.create_appointment_card(row)
            except Exception as e:
                print(f"Lỗi load danh sách: {e}")
            finally:
                db.close()

    def create_appointment_card(self, appt):
        """Tạo card lịch hẹn đẹp như hình mẫu"""
        card = ctk.CTkFrame(self.scroll_list, fg_color="white", corner_radius=12, border_width=1, border_color="#f1f5f9")
        card.pack(fill="x", pady=8, padx=5)
        
        # Cột trái: Icon và thông tin
        c_left = ctk.CTkFrame(card, fg_color="transparent")
        c_left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(c_left, text="📅", font=("Arial", 24)).pack(side="left", padx=(0, 15))
        
        info_v = ctk.CTkFrame(c_left, fg_color="transparent")
        info_v.pack(side="left")
        ctk.CTkLabel(info_v, text=appt[3] if appt[3] else "Dịch vụ", font=("Arial", 15, "bold")).pack(anchor="w")
        ctk.CTkLabel(info_v, text=f"👤 {appt[1]}  •  🚗 {appt[2]}", font=("Arial", 13), text_color="#64748b").pack(anchor="w")

        # Cột phải: Thời gian và nút xóa
        c_right = ctk.CTkFrame(card, fg_color="transparent")
        c_right.pack(side="right", padx=20)
        
        dt = appt[4]
        date_str = dt.strftime('%d/%m/%Y') if dt else "N/A"
        time_str = dt.strftime('%H:%M') if dt else "--:--"
        
        time_v = ctk.CTkFrame(c_right, fg_color="transparent")
        time_v.pack(side="left", padx=20)
        ctk.CTkLabel(time_v, text=f"🕒 {time_str}", font=("Arial", 14, "bold")).pack(anchor="e")
        ctk.CTkLabel(time_v, text=date_str, font=("Arial", 12), text_color="#64748b").pack(anchor="e")
        
        ctk.CTkButton(c_right, text="🗑", width=30, text_color="#ef4444", fg_color="transparent", 
                      hover_color="#fee2e2", command=lambda: self.delete_appointment(appt[0])).pack(side="right")

    def open_appointment_modal(self):
        """Mở form thiết lập lịch hẹn chuyên nghiệp"""
        modal = ctk.CTkToplevel(self)
        modal.title("Tạo lịch hẹn mới")
        modal.geometry("650x600")
        modal.grab_set()

        ctk.CTkLabel(modal, text="THÔNG TIN CHI TIẾT LỊCH HẸN", font=("Arial", 20, "bold"), text_color="#2563eb").pack(pady=20)

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40)

        # Lấy danh sách dịch vụ từ DB để đưa vào ComboBox
        service_list = []
        db = connect_db()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT id, service_name FROM services")
            service_data = cursor.fetchall() # Dạng [(1, 'Rửa xe'), (2, 'Thay lốp')...]
            service_list = [s[1] for s in service_data]
            db.close()

        inputs = {}

        # Layout 2 cột cho các thông tin cơ bản
        row1 = ctk.CTkFrame(container, fg_color="transparent"); row1.pack(fill="x", pady=5)
        
        # Tên khách
        c1 = ctk.CTkFrame(row1, fg_color="transparent"); c1.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(c1, text="Họ và tên *", text_color="#64748b").pack(anchor="w")
        inputs['name'] = ctk.CTkEntry(c1, height=40); inputs['name'].pack(fill="x", pady=5)

        # Số điện thoại (Để kiểm tra trùng)
        c2 = ctk.CTkFrame(row1, fg_color="transparent"); c2.pack(side="left", expand=True, fill="x", padx=(10, 0))
        ctk.CTkLabel(c2, text="Số điện thoại *", text_color="#64748b").pack(anchor="w")
        inputs['phone'] = ctk.CTkEntry(c2, height=40); inputs['phone'].pack(fill="x", pady=5)

        # Biển số xe
        ctk.CTkLabel(container, text="Biển số xe *", text_color="#64748b").pack(anchor="w", pady=(10, 0))
        inputs['plate'] = ctk.CTkEntry(container, height=40, placeholder_text="VD: 30A-123.45"); inputs['plate'].pack(fill="x", pady=5)

        # Chọn dịch vụ có sẵn
        ctk.CTkLabel(container, text="Dịch vụ yêu cầu *", text_color="#64748b").pack(anchor="w", pady=(10, 0))
        inputs['service'] = ctk.CTkComboBox(container, height=40, values=service_list); inputs['service'].pack(fill="x", pady=5)

        # Ngày và Giờ
        row2 = ctk.CTkFrame(container, fg_color="transparent"); row2.pack(fill="x", pady=10)
        
        c3 = ctk.CTkFrame(row2, fg_color="transparent"); c3.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(c3, text="Ngày hẹn (YYYY-MM-DD) *", text_color="#64748b").pack(anchor="w")
        inputs['date'] = ctk.CTkEntry(c3, height=40); inputs['date'].insert(0, datetime.now().strftime("%Y-%m-%d")); inputs['date'].pack(fill="x", pady=5)

        c4 = ctk.CTkFrame(row2, fg_color="transparent"); c4.pack(side="left", expand=True, fill="x", padx=(10, 0))
        ctk.CTkLabel(c4, text="Giờ hẹn (HH:MM) *", text_color="#64748b").pack(anchor="w")
        inputs['time'] = ctk.CTkEntry(c4, height=40); inputs['time'].insert(0, "08:30"); inputs['time'].pack(fill="x", pady=5)

        # Nút xác nhận
        btn_save = ctk.CTkButton(modal, text="Tạo lịch hẹn", fg_color="#2563eb", height=45, corner_radius=8,
                                 font=("Arial", 14, "bold"), command=lambda: self.save_appointment(inputs, modal, service_data))
        btn_save.pack(pady=30, padx=40, fill="x")

    def save_appointment(self, f, win, service_data):
        """Xử lý logic trùng khách hàng và lưu dữ liệu"""
        name, phone, plate = f['name'].get().strip(), f['phone'].get().strip(), f['plate'].get().strip()
        selected_sv_name = f['service'].get()
        appt_dt = f['date'].get() + " " + f['time'].get()

        if not (name and phone and plate):
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập đầy đủ thông tin!"); return

        # Tìm service_id từ tên dịch vụ đã chọn
        sv_id = next((s[0] for s in service_data if s[1] == selected_sv_name), None)

        db = connect_db()
        if db:
            try:
                cursor = db.cursor()
                db.start_transaction()

                # 1. Kiểm tra trùng khách hàng dựa trên tên + SĐT
                cursor.execute("SELECT id FROM customers WHERE full_name = %s AND phone = %s", (name, phone))
                cus_res = cursor.fetchone()

                if cus_res:
                    cus_id = cus_res[0]
                    # Nếu trùng: Tăng số lần tham gia dịch vụ (visit_count)
                    cursor.execute("UPDATE customers SET visit_count = visit_count + 1 WHERE id = %s", (cus_id,))
                else:
                    # Nếu mới: Tạo khách hàng mới
                    cursor.execute("INSERT INTO customers (full_name, phone, visit_count) VALUES (%s, %s, 1)", (name, phone))
                    cus_id = cursor.lastrowid
                cursor.execute("SELECT plate_number FROM cars WHERE plate_number = %s", (plate,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO cars (plate_number, customer_id) VALUES (%s, %s)", (plate, cus_id))

                
                sql_appt = "INSERT INTO appointments (customer_id, car_plate, service_id, appointment_date, status) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_appt, (cus_id, plate, sv_id, appt_dt, "Chờ xác nhận"))

                db.commit()
                win.destroy()
                self.load_appointments()
                
            except Exception as e:
                db.rollback()
                messagebox.showerror("Lỗi", f"Không thể lưu lịch hẹn: {e}")
            finally:
                db.close()

    def delete_appointment(self, appt_id):
        if messagebox.askyesno("Xác nhận", "Bạn có muốn xóa lịch hẹn này?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM appointments WHERE id = %s", (appt_id,))
                db.commit()
                db.close()
                self.load_appointments()