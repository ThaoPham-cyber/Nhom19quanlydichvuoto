import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from tkcalendar import DateEntry
import re
from database import connect_db


class AppointmentFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#f3f4f6")
        self.parent_app = master

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ===== HEADER =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=15)

        ctk.CTkLabel(header, text="Lịch hẹn", font=("Arial", 24, "bold")).pack(side="left")
        
        # Nút xem lịch sử bàn giao
        history_btn = ctk.CTkButton(header, text="📜 Lịch sử bàn giao",
                                    fg_color="#8b5cf6", hover_color="#7c3aed",
                                    command=self.show_handover_history)
        history_btn.pack(side="right", padx=5)
        
        ctk.CTkButton(header, text="+ Tạo lịch hẹn",
                      fg_color="#2563eb",
                      command=self.open_modal).pack(side="right", padx=5)

        # ===== SEARCH =====
        self.search = ctk.CTkEntry(self, placeholder_text="🔍 Tìm khách / biển số...")
        self.search.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 10))
        self.search.bind("<KeyRelease>", lambda e: self.load())

        # ===== LIST =====
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 20))

        self.load()

    # ================= LOAD =================
    def load(self):
        """Tải danh sách lịch hẹn chưa bàn giao và chưa hủy"""
        for w in self.list_frame.winfo_children():
            w.destroy()

        db = connect_db()
        if not db:
            return

        cursor = db.cursor()
        search = f"%{self.search.get()}%"

        # Chỉ lấy các lịch hẹn chưa bàn giao và chưa hủy
        cursor.execute("""
            SELECT a.id, c.full_name, a.car_plate,
                   COALESCE(s.service_name,'Không rõ'),
                   a.appointment_date, a.status, s.price, s.id
            FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            LEFT JOIN services s ON a.service_id = s.id
            WHERE (c.full_name LIKE %s OR a.car_plate LIKE %s)
            AND a.status NOT IN ('Đã bàn giao', 'Hủy lịch')
            ORDER BY a.appointment_date DESC
        """, (search, search))

        appointments = cursor.fetchall()
        
        if not appointments:
            empty_label = ctk.CTkLabel(
                self.list_frame, 
                text="📭 Không có lịch hẹn nào đang hoạt động\n\nNhấn '+ Tạo lịch hẹn' để tạo mới",
                font=("Arial", 14), text_color="#64748b"
            )
            empty_label.pack(pady=50)
        else:
            for row in appointments:
                self.card(row)

        db.close()
    
    def show_handover_history(self):
        """Hiển thị lịch sử bàn giao"""
        history_window = ctk.CTkToplevel(self)
        history_window.title("Lịch sử bàn giao")
        history_window.geometry("900x500")
        history_window.attributes("-topmost", True)
        history_window.grab_set()
        history_window.configure(fg_color="white")
        
        header_frame = ctk.CTkFrame(history_window, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="📜 LỊCH SỬ BÀN GIAO", 
                    font=("Arial", 20, "bold"), text_color="#1e293b").pack(side="left")
        
        # Search
        search_frame = ctk.CTkFrame(history_window, fg_color="white", corner_radius=12, 
                                   border_width=1, border_color="#e2e8f0")
        search_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        search_entry = ctk.CTkEntry(search_frame, 
                                   placeholder_text="🔍 Tìm kiếm...",
                                   border_width=0, fg_color="transparent", height=40)
        search_entry.pack(fill="x", padx=15)
        
        # Table frame
        table_frame = ctk.CTkFrame(history_window, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Header
        headers = ["Mã LH", "Khách hàng", "Biển số", "Dịch vụ", "Ngày hẹn", "Giá", "Trạng thái"]
        
        header_frame = ctk.CTkFrame(table_frame, fg_color="#f1f5f9", height=40)
        header_frame.pack(fill="x", padx=1, pady=(1, 0))
        
        for i, text in enumerate(headers):
            ctk.CTkLabel(header_frame, text=text, font=("Arial", 12, "bold"), 
                        text_color="#64748b").grid(row=0, column=i, padx=10, pady=10, sticky="w")
            header_frame.grid_columnconfigure(i, weight=1)
        
        scroll_frame = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        
        db = connect_db()
        if db:
            cursor = db.cursor()
            
            def load_history(*args):
                for w in scroll_frame.winfo_children():
                    w.destroy()
                
                search = f"%{search_entry.get()}%"
                cursor.execute("""
                    SELECT a.id, c.full_name, a.car_plate,
                           COALESCE(s.service_name,'Không rõ'),
                           a.appointment_date, s.price, a.status
                    FROM appointments a
                    JOIN customers c ON a.customer_id = c.id
                    LEFT JOIN services s ON a.service_id = s.id
                    WHERE (c.full_name LIKE %s OR a.car_plate LIKE %s)
                    AND a.status = 'Đã bàn giao'
                    ORDER BY a.appointment_date DESC
                """, (search, search))
                
                appointments = cursor.fetchall()
                
                if not appointments:
                    ctk.CTkLabel(scroll_frame, text="📭 Không có dữ liệu bàn giao", 
                                font=("Arial", 14), text_color="#64748b").pack(pady=50)
                    return
                
                for idx, appt in enumerate(appointments):
                    row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent", height=35)
                    row_frame.pack(fill="x", pady=2)
                    
                    dt = appt[4]
                    if isinstance(dt, str):
                        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    
                    ctk.CTkLabel(row_frame, text=f"AP{appt[0]:04d}", font=("Arial", 12),
                                text_color="#2563eb").grid(row=0, column=0, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=appt[1], font=("Arial", 12)).grid(row=0, column=1, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=appt[2], font=("Arial", 12)).grid(row=0, column=2, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=appt[3], font=("Arial", 11)).grid(row=0, column=3, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=dt.strftime("%d/%m/%Y %H:%M"), font=("Arial", 11)).grid(row=0, column=4, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=f"{int(appt[5]):,} đ" if appt[5] else "0 đ", 
                                font=("Arial", 11, "bold"), text_color="#10b981").grid(row=0, column=5, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text="✅ Đã bàn giao", font=("Arial", 11),
                                text_color="#10b981").grid(row=0, column=6, padx=10, pady=8, sticky="w")
                    
                    if idx < len(appointments) - 1:
                        ctk.CTkFrame(scroll_frame, height=1, fg_color="#e2e8f0").pack(fill="x", padx=10)
            
            search_entry.bind("<KeyRelease>", lambda e: load_history())
            load_history()
            db.close()

    # ================= CARD =================
    def card(self, appt):
        card = ctk.CTkFrame(self.list_frame, fg_color="white",
                            corner_radius=12, border_width=1)
        card.pack(fill="x", pady=8, padx=5)

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(left, text=appt[3],
                     font=("Arial", 16, "bold")).pack(anchor="w")

        ctk.CTkLabel(left,
                     text=f"{appt[1]} • {appt[2]}",
                     text_color="#6b7280").pack(anchor="w")

        status = appt[5]
        color = {
            "Chờ xác nhận": "#facc15",
            "Đã xác nhận": "#60a5fa",
            "Đã hoàn thành": "#22c55e",
            "Đã bàn giao": "#10b981",
            "Hủy lịch": "#ef4444"
        }.get(status, "#e5e7eb")

        ctk.CTkLabel(left, text=status,
                     fg_color=color,
                     corner_radius=6,
                     padx=10).pack(anchor="w", pady=5)

        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=15, pady=10)

        dt = appt[4]
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")

        ctk.CTkLabel(right, text=dt.strftime("%d/%m/%Y")).pack(anchor="e")
        ctk.CTkLabel(right, text=dt.strftime("%H:%M")).pack(anchor="e")
        
        # Price
        if appt[6]:
            ctk.CTkLabel(right, text=f"{int(appt[6]):,} đ", 
                        font=("Arial", 12, "bold"), text_color="#10b981").pack(anchor="e", pady=2)

        btn = ctk.CTkFrame(right, fg_color="transparent")
        btn.pack(anchor="e", pady=5)

        if status == "Chờ xác nhận":
            ctk.CTkButton(btn, text="Xác nhận",
                          command=lambda: self.update_status(appt[0], "Đã xác nhận")).pack(side="left", padx=3)

            ctk.CTkButton(btn, text="Hủy",
                          fg_color="#ef4444",
                          command=lambda: self.update_status(appt[0], "Hủy lịch")).pack(side="left", padx=3)

        elif status == "Đã xác nhận":
            ctk.CTkButton(btn, text="Hoàn thành",
                          fg_color="#10b981",
                          command=lambda: self.complete_appointment(appt[0])).pack(side="left")

        elif status == "Đã hoàn thành":
            ctk.CTkButton(btn, text="Bàn giao",
                          fg_color="#2563eb",
                          command=lambda: self.handover_appointment(appt[0])).pack(side="left")

    def update_status(self, appt_id, status):
        """Cập nhật trạng thái lịch hẹn"""
        db = connect_db()
        if not db:
            messagebox.showerror("Lỗi", "Không kết nối DB")
            return

        cursor = db.cursor()
        try:
            cursor.execute("""
                UPDATE appointments 
                SET status=%s 
                WHERE id=%s
            """, (status, appt_id))
            db.commit()
            messagebox.showinfo("Thành công", f"Đã {status.lower()} lịch hẹn!")
            self.load()
            
            # Refresh dashboard if exists
            if hasattr(self.parent_app, 'refresh_dashboard'):
                self.parent_app.refresh_dashboard()
                
        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", str(e))
        finally:
            db.close()

    def complete_appointment(self, appt_id):
        """Đánh dấu hoàn thành"""
        if messagebox.askyesno("Xác nhận", "Xác nhận hoàn thành dịch vụ?"):
            db = connect_db()
            if not db:
                messagebox.showerror("Lỗi", "Không kết nối DB")
                return

            cursor = db.cursor()
            try:
                # Cập nhật trạng thái thành "Đã hoàn thành"
                cursor.execute("""
                    UPDATE appointments 
                    SET status = 'Đã hoàn thành', progress_percent = 100
                    WHERE id = %s
                """, (appt_id,))
                
                db.commit()
                messagebox.showinfo("Thành công", "Đã hoàn thành dịch vụ!")
                self.load()
                
                # Refresh dashboard
                if hasattr(self.parent_app, 'refresh_dashboard'):
                    self.parent_app.refresh_dashboard()
                
            except Exception as e:
                db.rollback()
                messagebox.showerror("Lỗi", str(e))
            finally:
                db.close()

    def handover_appointment(self, appt_id):
        """Bàn giao - Tạo hóa đơn và chuyển sang thanh toán"""
        if messagebox.askyesno("Xác nhận", "Bàn giao xe và tạo hóa đơn thanh toán?"):
            db = connect_db()
            if not db:
                messagebox.showerror("Lỗi", "Không thể kết nối database!")
                return
            
            cursor = db.cursor()
            try:
                # Lấy thông tin appointment
                cursor.execute("""
                    SELECT a.id, a.customer_id, a.car_plate, a.appointment_date,
                           s.id as service_id, s.service_name, s.price
                    FROM appointments a
                    LEFT JOIN services s ON a.service_id = s.id
                    WHERE a.id = %s
                """, (appt_id,))
                appt_data = cursor.fetchone()
                
                if not appt_data:
                    messagebox.showerror("Lỗi", "Không tìm thấy thông tin lịch hẹn!")
                    return
                
                # Kiểm tra xem đã có invoice chưa
                cursor.execute("SELECT id, status FROM invoices WHERE appointment_id = %s", (appt_id,))
                existing_invoice = cursor.fetchone()
                
                if existing_invoice:
                    invoice_id = existing_invoice[0]
                    if existing_invoice[1] == "Đã thanh toán":
                        # Nếu đã thanh toán thì chỉ cập nhật status appointment
                        cursor.execute("""
                            UPDATE appointments SET status = 'Đã bàn giao' WHERE id = %s
                        """, (appt_id,))
                        db.commit()
                        messagebox.showinfo("Thông báo", "Hóa đơn đã được thanh toán trước đó!")
                    else:
                        # Cập nhật status nếu cần
                        cursor.execute("""
                            UPDATE appointments SET status = 'Đã bàn giao' WHERE id = %s
                        """, (appt_id,))
                        db.commit()
                        messagebox.showinfo("Thành công", "Đã cập nhật trạng thái bàn giao!")
                else:
                    # Tạo invoice mới với status "Chưa thanh toán"
                    cursor.execute("""
                        INSERT INTO invoices (appointment_id, customer_id, total_amount, status, created_at)
                        VALUES (%s, %s, %s, 'Chưa thanh toán', NOW())
                    """, (appt_id, appt_data[1], appt_data[6]))
                    invoice_id = cursor.lastrowid
                    
                    # Thêm invoice item
                    cursor.execute("""
                        INSERT INTO invoice_items (invoice_id, service_id, service_name, price, quantity)
                        VALUES (%s, %s, %s, %s, 1)
                    """, (invoice_id, appt_data[4], appt_data[5], appt_data[6]))
                    
                    # Cập nhật trạng thái appointment thành "Đã bàn giao"
                    cursor.execute("""
                        UPDATE appointments 
                        SET status = 'Đã bàn giao'
                        WHERE id = %s
                    """, (appt_id,))
                    
                    db.commit()
                    messagebox.showinfo("Thành công", f"Đã tạo hóa đơn HD{invoice_id:04d}!\nVui lòng vào mục Thanh toán để hoàn tất.")
                
                # Refresh appointment list (sẽ ẩn các lịch đã bàn giao)
                self.load()
                
                # Chuyển sang tab Payment nếu có
                if hasattr(self.parent_app, 'show_payment_tab'):
                    self.parent_app.show_payment_tab()
                
                # Refresh dashboard
                if hasattr(self.parent_app, 'refresh_dashboard'):
                    self.parent_app.refresh_dashboard()
                
                # Refresh payment list
                if hasattr(self.parent_app, 'refresh_payments'):
                    self.parent_app.refresh_payments()
                
            except Exception as e:
                db.rollback()
                messagebox.showerror("Lỗi", f"Không thể tạo hóa đơn: {e}")
                print(f"Lỗi chi tiết: {e}")
            finally:
                db.close()

    # ================= CREATE MODAL =================
    def open_modal(self):
        self.modal_window = ctk.CTkToplevel(self)
        self.modal_window.title("Tạo Lịch Hẹn Mới")
        self.modal_window.geometry("650x900")
        self.modal_window.attributes("-topmost", True)
        self.modal_window.grab_set()

        self.modal_window.grid_columnconfigure(0, weight=1)
        self.modal_window.grid_rowconfigure(0, weight=1)

        main_scroll = ctk.CTkScrollableFrame(self.modal_window, fg_color="transparent")
        main_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_scroll.grid_columnconfigure(0, weight=1)

        # Customer Information
        ctk.CTkLabel(main_scroll, text="THÔNG TIN KHÁCH HÀNG", 
                     font=("Arial", 15, "bold"), text_color="#2563eb").grid(row=0, column=0, sticky="w", pady=(10, 15))
        
        self.ent_name = self.create_input_group(main_scroll, "Họ và tên *:", "Nhập tên khách hàng", 1)
        self.ent_phone = self.create_input_group(main_scroll, "Số điện thoại *:", "VD: 0912345678", 3)
        self.ent_email = self.create_input_group(main_scroll, "Email:", "VD: example@email.com", 5)  # Thêm email
        
        # Car Information
        ctk.CTkLabel(main_scroll, text="THÔNG TIN XE", 
                     font=("Arial", 15, "bold"), text_color="#2563eb").grid(row=7, column=0, sticky="w", pady=(10, 15))
        
        self.ent_plate = self.create_input_group(main_scroll, "Biển số xe *:", "VD: 30A-123.45", 8)
        self.ent_brand = self.create_input_group(main_scroll, "Hãng xe:", "VD: Toyota, Honda, Ford...", 10)
        self.ent_model = self.create_input_group(main_scroll, "Mẫu xe:", "VD: Vios, Civic, Ranger...", 12)
        self.ent_year = self.create_input_group(main_scroll, "Năm sản xuất:", "VD: 2020, 2021...", 14)

        # Service Selection
        ctk.CTkLabel(main_scroll, text="CHỌN DỊCH VỤ", 
                     font=("Arial", 15, "bold"), text_color="#2563eb").grid(row=16, column=0, sticky="w", pady=(10, 5))
        
        svc_frame = ctk.CTkFrame(main_scroll, fg_color="#f8fafc", border_width=1, border_color="#e2e8f0")
        svc_frame.grid(row=17, column=0, sticky="ew", pady=5)
        svc_frame.grid_columnconfigure(0, weight=1)

        svc_scroll = ctk.CTkScrollableFrame(svc_frame, height=150, fg_color="transparent")
        svc_scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, service_name, price FROM services WHERE status = 1")
        services = cursor.fetchall()
        db.close()

        self.svc_vars = {}
        self.svc_prices = {}
        
        count_label = ctk.CTkLabel(main_scroll, text="Đã chọn: 0 dịch vụ", font=("Arial", 11, "italic"), text_color="#64748b")
        count_label.grid(row=18, column=0, sticky="e")

        def update_count(*args):
            count = sum(v.get() for v in self.svc_vars.values())
            count_label.configure(text=f"Đã chọn: {count} dịch vụ")
            update_total()

        for sid, name_svc, price in services:
            var = ctk.BooleanVar()
            var.trace_add("write", update_count)
            
            frame = ctk.CTkFrame(svc_scroll, fg_color="transparent")
            frame.pack(fill="x", pady=4, padx=10)
            
            cb = ctk.CTkCheckBox(frame, text=name_svc, variable=var, font=("Arial", 13))
            cb.pack(side="left")
            
            price_label = ctk.CTkLabel(frame, text=f"{int(price):,} đ", font=("Arial", 11), text_color="#10b981")
            price_label.pack(side="right")
            
            self.svc_vars[sid] = var
            self.svc_prices[sid] = price

        # Time
        ctk.CTkLabel(main_scroll, text="THỜI GIAN HẸN", 
                     font=("Arial", 15, "bold"), text_color="#2563eb").grid(row=19, column=0, sticky="w", pady=(20, 5))
        
        time_container = ctk.CTkFrame(main_scroll, fg_color="transparent")
        time_container.grid(row=20, column=0, sticky="ew")
        time_container.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(time_container, text="Ngày hẹn:", font=("Arial", 12)).grid(row=0, column=0, sticky="w")
        self.date_pick = DateEntry(time_container, date_pattern="yyyy-mm-dd", background='#2563eb', foreground='white')
        self.date_pick.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=2)

        ctk.CTkLabel(time_container, text="Giờ hẹn (HH:MM):", font=("Arial", 12)).grid(row=0, column=1, sticky="w")
        self.time_ent = ctk.CTkEntry(time_container, placeholder_text="08:30", height=35)
        self.time_ent.grid(row=1, column=1, sticky="ew", pady=2)

        # Total
        self.total_label = ctk.CTkLabel(main_scroll, text="Tổng tiền: 0 đ", font=("Arial", 14, "bold"), text_color="#ef4444")
        self.total_label.grid(row=21, column=0, sticky="e", pady=(10, 0))
        
        def update_total():
            total = sum(self.svc_prices[sid] for sid, v in self.svc_vars.items() if v.get())
            self.total_label.configure(text=f"Tổng tiền: {int(total):,} đ")
        
        btn_save = ctk.CTkButton(main_scroll, text="XÁC NHẬN TẠO LỊCH", font=("Arial", 14, "bold"), 
                                 fg_color="#2563eb", hover_color="#1d4ed8", height=50, 
                                 command=self.save_appointment)
        btn_save.grid(row=22, column=0, sticky="ew", pady=30)

    def create_input_group(self, parent, label_text, placeholder, row):
        ctk.CTkLabel(parent, text=label_text, font=("Arial", 12)).grid(row=row, column=0, sticky="w")
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=35)
        entry.grid(row=row+1, column=0, sticky="ew", pady=(2, 12))
        return entry

    def save_appointment(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()
        plate = self.ent_plate.get().strip().upper()
        brand = self.ent_brand.get().strip()
        model = self.ent_model.get().strip()
        year_str = self.ent_year.get().strip()
        selected_services = [sid for sid, v in self.svc_vars.items() if v.get()]
        
        if not name or not phone or not plate:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin bắt buộc!")
            return
        
        if not selected_services:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 dịch vụ!")
            return
        
        if not phone.isdigit() or len(phone) < 9:
            messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ!")
            return
        
        current_year = datetime.now().year
        year = None
        if year_str:
            if not year_str.isdigit():
                messagebox.showerror("Lỗi", "Năm sản xuất phải là số!")
                return
            year = int(year_str)
            if year < 1900 or year > current_year + 1:
                messagebox.showerror("Lỗi", f"Năm sản xuất không hợp lệ (1900-{current_year})!")
                return
        
        try:
            dt_str = self.date_pick.get() + " " + self.time_ent.get()
            appointment_date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            
            db = connect_db()
            cursor = db.cursor()
            
            # Customer
            cursor.execute("SELECT id, full_name, email FROM customers WHERE phone = %s", (phone,))
            result = cursor.fetchone()
            
            if result:
                customer_id = result[0]
                # Cập nhật tên và email nếu thay đổi
                update_fields = []
                params = []
                if result[1] != name:
                    update_fields.append("full_name = %s")
                    params.append(name)
                if email and (len(result) < 3 or result[2] != email):
                    update_fields.append("email = %s")
                    params.append(email)
                if update_fields:
                    params.append(customer_id)
                    cursor.execute(f"UPDATE customers SET {', '.join(update_fields)} WHERE id = %s", params)
            else:
                cursor.execute("INSERT INTO customers (full_name, phone, email, visit_count) VALUES (%s, %s, %s, 1)", (name, phone, email))
                customer_id = cursor.lastrowid
            
            # Car
            cursor.execute("SELECT plate_number FROM cars WHERE plate_number = %s", (plate,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO cars (plate_number, brand, model, year, customer_id) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (plate, brand if brand else None, model if model else None, year, customer_id))
            
            # Appointments
            for service_id in selected_services:
                cursor.execute("""
                    INSERT INTO appointments (customer_id, car_plate, service_id, appointment_date, status, progress_percent)
                    VALUES (%s, %s, %s, %s, 'Chờ xác nhận', 0)
                """, (customer_id, plate, service_id, appointment_date))
            
            db.commit()
            db.close()
            
            messagebox.showinfo("Thành công", f"Đã tạo {len(selected_services)} lịch hẹn!")
            self.modal_window.destroy()
            self.load()
            
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))