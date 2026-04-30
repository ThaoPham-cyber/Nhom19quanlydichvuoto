import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from tkcalendar import DateEntry
import re
from database import connect_db


class AppointmentFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#f3f4f6")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ===== HEADER =====
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=15)

        ctk.CTkLabel(header, text="Lịch hẹn", font=("Arial", 24, "bold")).pack(side="left")

        ctk.CTkButton(header, text="+ Tạo lịch hẹn",
                      fg_color="#2563eb",
                      command=self.open_modal).pack(side="right")

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
        for w in self.list_frame.winfo_children():
            w.destroy()

        db = connect_db()
        if not db:
            return

        cursor = db.cursor()
        search = f"%{self.search.get()}%"

        cursor.execute("""
            SELECT a.id, c.full_name, a.car_plate,
                   COALESCE(s.service_name,'Không rõ'),
                   a.appointment_date, a.status
            FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            LEFT JOIN services s ON a.service_id = s.id
            WHERE c.full_name LIKE %s OR a.car_plate LIKE %s
            ORDER BY a.appointment_date DESC
        """, (search, search))

        for row in cursor.fetchall():
            self.card(row)

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
            "Đã hoàn thành": "#22c55e"
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

        btn = ctk.CTkFrame(right, fg_color="transparent")
        btn.pack(anchor="e", pady=5)

        if status == "Chờ xác nhận":
            ctk.CTkButton(btn, text="Xác nhận",
                          command=lambda: self.update(appt[0], "Đã xác nhận")).pack(side="left", padx=3)

            ctk.CTkButton(btn, text="Hủy",
                          fg_color="#ef4444",
                          command=lambda: self.update(appt[0], "Hủy lịch")).pack(side="left", padx=3)

        elif status == "Đã xác nhận":
            ctk.CTkButton(btn, text="Hoàn thành",
                          fg_color="#10b981",
                          command=lambda: self.update(appt[0], "Đã hoàn thành")).pack(side="left")

        elif status == "Đã hoàn thành":
            ctk.CTkButton(btn, text="Bàn giao",
                          fg_color="#2563eb",
                          command=lambda: self.update(appt[0], "Đã bàn giao")).pack(side="left")

    # ================= UPDATE (FIX FULL) =================
    def update(self, appt_id, status):
        db = connect_db()
        if not db:
            messagebox.showerror("Lỗi", "Không kết nối DB")
            return

        cursor = db.cursor()

        try:
            if status == "Đã bàn giao":

                # ✅ check theo appointment_id (chuẩn)
                cursor.execute("""
                    SELECT COUNT(*) FROM service_history 
                    WHERE appointment_id=%s
                """, (appt_id,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Thông báo", "Lịch này đã bàn giao rồi!")
                    return

                # ✅ insert đầy đủ + price
                cursor.execute("""
                    INSERT INTO service_history
                    (appointment_id, customer_id, service_name, plate_number,
                     service_date, service_time, price, status)
                    SELECT 
                        a.id,
                        a.customer_id,
                        COALESCE(s.service_name,'Không rõ'),
                        a.car_plate,
                        DATE(a.appointment_date),
                        TIME(a.appointment_date),
                        COALESCE(s.price,0),
                        'Hoàn thành'
                    FROM appointments a
                    LEFT JOIN services s ON a.service_id = s.id
                    WHERE a.id=%s
                """, (appt_id,))

                # ✅ XÓA khỏi appointments
                cursor.execute("DELETE FROM appointments WHERE id=%s", (appt_id,))

            else:
                cursor.execute("""
                    UPDATE appointments 
                    SET status=%s 
                    WHERE id=%s
                """, (status, appt_id))

            db.commit()
            self.load()

        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", str(e))
        finally:
            db.close()

   # ================= CREATE (FIX RESPONSIVE) =================
    def open_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Tạo Lịch Hẹn Mới")
        modal.geometry("550x700")
        modal.attributes("-topmost", True)
        modal.grab_set()

        # Cho phép modal co dãn cột chính
        modal.grid_columnconfigure(0, weight=1)
        modal.grid_rowconfigure(0, weight=1)

        # Toàn bộ nội dung nằm trong ScrollableFrame để không bị mất nội dung khi màn hình bé
        main_scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        main_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_scroll.grid_columnconfigure(0, weight=1)

        # --- PHẦN 1: THÔNG TIN KHÁCH HÀNG ---
        ctk.CTkLabel(main_scroll, text="THÔNG TIN KHÁCH HÀNG", 
                     font=("Arial", 15, "bold"), text_color="#2563eb").grid(row=0, column=0, sticky="w", pady=(10, 15))
        
        # Helper để tạo các hàng nhập liệu co dãn
        def create_input_group(parent, label_text, placeholder, row):
            ctk.CTkLabel(parent, text=label_text, font=("Arial", 12)).grid(row=row, column=0, sticky="w")
            entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=35)
            entry.grid(row=row+1, column=0, sticky="ew", pady=(2, 12))
            return entry

        name = create_input_group(main_scroll, "Họ và tên:", "Nhập tên khách hàng", 1)
        phone = create_input_group(main_scroll, "Số điện thoại:", "VD: 0912345678", 3)
        plate = create_input_group(main_scroll, "Biển số xe:", "VD: 30A-123.45", 5)

        # --- PHẦN 2: CHỌN DỊCH VỤ ---
        ctk.CTkLabel(main_scroll, text="CHỌN DỊCH VỤ", 
                     font=("Arial", 15, "bold"), text_color="#2563eb").grid(row=7, column=0, sticky="w", pady=(10, 5))
        
        svc_frame = ctk.CTkFrame(main_scroll, fg_color="#f8fafc", border_width=1, border_color="#e2e8f0")
        svc_frame.grid(row=8, column=0, sticky="ew", pady=5)
        svc_frame.grid_columnconfigure(0, weight=1)

        svc_scroll = ctk.CTkScrollableFrame(svc_frame, height=150, fg_color="transparent")
        svc_scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Lấy dữ liệu dịch vụ
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, service_name FROM services")
        services = cursor.fetchall()
        db.close()

        svc_vars = {}
        count_label = ctk.CTkLabel(main_scroll, text="Đã chọn: 0 dịch vụ", font=("Arial", 11, "italic"), text_color="#64748b")
        count_label.grid(row=9, column=0, sticky="e")

        def update_count(*_):
            count = sum(v.get() for v in svc_vars.values())
            count_label.configure(text=f"Đã chọn: {count} dịch vụ")

        for sid, name_svc in services:
            var = ctk.BooleanVar()
            var.trace_add("write", update_count)
            cb = ctk.CTkCheckBox(svc_scroll, text=name_svc, variable=var, font=("Arial", 13))
            cb.pack(anchor="w", pady=4, padx=10)
            svc_vars[sid] = var

        # --- PHẦN 3: THỜI GIAN (CHIA CỘT 50/50) ---
        ctk.CTkLabel(main_scroll, text="THỜI GIAN HẸN", 
                     font=("Arial", 15, "bold"), text_color="#2563eb").grid(row=10, column=0, sticky="w", pady=(20, 5))
        
        time_container = ctk.CTkFrame(main_scroll, fg_color="transparent")
        time_container.grid(row=11, column=0, sticky="ew")
        time_container.grid_columnconfigure((0, 1), weight=1)

        # Ngày
        ctk.CTkLabel(time_container, text="Ngày hẹn:", font=("Arial", 12)).grid(row=0, column=0, sticky="w")
        date_pick = DateEntry(time_container, date_pattern="yyyy-mm-dd", background='#2563eb', foreground='white')
        date_pick.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=2)

        # Giờ
        ctk.CTkLabel(time_container, text="Giờ hẹn (HH:MM):", font=("Arial", 12)).grid(row=0, column=1, sticky="w")
        time_ent = ctk.CTkEntry(time_container, placeholder_text="08:30", height=35)
        time_ent.grid(row=1, column=1, sticky="ew", pady=2)

        # --- NÚT XÁC NHẬN ---
        def save_action():
            # (Giữ nguyên logic kiểm tra dữ liệu như cũ)
            if not name.get() or not phone.get() or not plate.get():
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!"); return
            
            selected = [sid for sid, v in svc_vars.items() if v.get()]
            if not selected:
                messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 dịch vụ!"); return
            
            try:
                dt_obj = datetime.strptime(date_pick.get()+" "+time_ent.get(), "%Y-%m-%d %H:%M")
                db_conn = connect_db()
                curr = db_conn.cursor()
                
                # Check khách hàng
                curr.execute("SELECT id FROM customers WHERE phone=%s", (phone.get(),))
                res = curr.fetchone()
                cus_id = res[0] if res else None
                if not cus_id:
                    curr.execute("INSERT INTO customers(full_name, phone) VALUES(%s,%s)", (name.get(), phone.get()))
                    cus_id = curr.lastrowid
                
                # Insert lịch hẹn
                for sid in selected:
                    curr.execute("""INSERT INTO appointments(customer_id, car_plate, service_id, appointment_date, status) 
                                    VALUES (%s,%s,%s,%s,'Chờ xác nhận')""", (cus_id, plate.get(), sid, dt_obj))
                
                db_conn.commit()
                db_conn.close()
                modal.destroy()
                self.load()
            except ValueError:
                messagebox.showerror("Lỗi", "Sai định dạng giờ (HH:MM)!")
            except Exception as e:
                messagebox.showerror("Lỗi DB", str(e))

        btn_save = ctk.CTkButton(main_scroll, text="XÁC NHẬN TẠO LỊCH", font=("Arial", 14, "bold"), 
                                 fg_color="#2563eb", hover_color="#1d4ed8", height=50, command=save_action)
        btn_save.grid(row=12, column=0, sticky="ew", pady=30)