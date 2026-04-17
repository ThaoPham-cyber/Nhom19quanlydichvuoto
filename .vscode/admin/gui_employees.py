import customtkinter as ctk
from database import connect_db
from tkinter import messagebox
from datetime import datetime

class EmployeeFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=35, pady=(25, 15))
        
        title_v = ctk.CTkFrame(header, fg_color="transparent")
        title_v.pack(side="left")
        ctk.CTkLabel(title_v, text="Quản lý nhân viên", font=("Arial", 28, "bold"), text_color="#0f172a").pack(anchor="w")
        self.lbl_total = ctk.CTkLabel(title_v, text="Tổng số nhân viên: 0", font=("Arial", 14), text_color="#64748b")
        self.lbl_total.pack(anchor="w")
        
        ctk.CTkButton(header, text="+ Thêm nhân viên", fg_color="#2563eb", hover_color="#1d4ed8",
                      font=("Arial", 13, "bold"), height=40, corner_radius=8,
                      command=lambda: self.open_employee_modal()).pack(side="right")

        # --- SEARCH ---
        filter_f = ctk.CTkFrame(self, fg_color="transparent")
        filter_f.grid(row=1, column=0, sticky="ew", padx=35, pady=(0, 20))
        self.ent_search = ctk.CTkEntry(filter_f, placeholder_text="🔍 Tìm theo mã, tên, SĐT, CCCD...", 
                                       height=45, fg_color="white", border_color="#e2e8f0")
        self.ent_search.pack(side="left", fill="x", expand=True)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_employees())

        # --- LIST ---
        self.scroll_list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_list.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
        
        self.load_employees()

    def load_employees(self):
        for w in self.scroll_list.winfo_children(): w.destroy()
        db = connect_db()
        if db:
            cursor = db.cursor()
            search = f"%{self.ent_search.get()}%"
            query = """SELECT id, employee_code, full_name, phone, cccd, email, 
                       position, department, salary, hire_date 
                       FROM employees 
                       WHERE (full_name LIKE %s OR employee_code LIKE %s OR cccd LIKE %s)"""
            cursor.execute(query, (search, search, search))
            rows = cursor.fetchall()
            for row in rows: self.create_employee_card(row)
            self.lbl_total.configure(text=f"Tổng số nhân viên: {len(rows)}")
            db.close()

    def create_employee_card(self, emp):
        # emp: (id, code, name, phone, cccd, email, pos, dept, sal, date)
        card = ctk.CTkFrame(self.scroll_list, fg_color="white", corner_radius=12, border_width=1, border_color="#f1f5f9")
        card.pack(fill="x", pady=8, padx=5)
        
        card.grid_columnconfigure(1, minsize=240) # Tên
        card.grid_columnconfigure(2, minsize=260) # Liên hệ
        card.grid_columnconfigure(3, minsize=220) # Lương/Ngày vào
        card.grid_columnconfigure(4, weight=1)

        # Avatar ký tự đầu
        ctk.CTkLabel(card, text=emp[2][0], width=50, height=50, corner_radius=25, fg_color="#eff6ff", 
                     text_color="#2563eb", font=("Arial", 16, "bold")).grid(row=0, column=0, padx=20, pady=20)

        # Thông tin chính
        c1 = ctk.CTkFrame(card, fg_color="transparent")
        c1.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(c1, text=emp[2], font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(c1, text=f"{emp[1]} • {emp[6]}", font=("Arial", 13), text_color="#64748b").pack(anchor="w")

        c2 = ctk.CTkFrame(card, fg_color="transparent")
        c2.grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(c2, text=f"📞 {emp[3]}", font=("Arial", 13)).pack(anchor="w")
        ctk.CTkLabel(c2, text=f"🪪 {emp[4] or 'N/A'}", font=("Arial", 13), text_color="#64748b").pack(anchor="w")

        c3 = ctk.CTkFrame(card, fg_color="transparent")
        c3.grid(row=0, column=3, sticky="w")
        hire_date = emp[9].strftime('%d/%m/%Y') if emp[9] else "N/A"
        ctk.CTkLabel(c3, text=f"📅 {hire_date}", font=("Arial", 13)).pack(anchor="w")
        ctk.CTkLabel(c3, text=f"💰 {int(emp[8]):,}đ", font=("Arial", 13), text_color="#64748b").pack(anchor="w")

        # --- NÚT THAO TÁC ICON MỚI ---
        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.grid(row=0, column=4, sticky="e", padx=20)
        
        # Xem chi tiết
        ctk.CTkButton(btn_f, text="👁", width=35, height=35, corner_radius=18, fg_color="#f0f9ff", 
                      text_color="#0369a1", hover_color="#e0f2fe", font=("Arial", 16),
                      command=lambda: self.view_details(emp)).pack(side="left", padx=3)
        
        # Sửa
        ctk.CTkButton(btn_f, text="✎", width=35, height=35, corner_radius=18, fg_color="#fefce8", 
                      text_color="#a16207", hover_color="#fef9c3", font=("Arial", 18),
                      command=lambda: self.open_employee_modal(emp)).pack(side="left", padx=3)
        
        # Xóa
        ctk.CTkButton(btn_f, text="×", width=35, height=35, corner_radius=18, fg_color="#fff1f2", 
                      text_color="#be123c", hover_color="#ffe4e6", font=("Arial", 22, "bold"),
                      command=lambda: self.delete_emp(emp[0], emp[2])).pack(side="left", padx=3)

    def view_details(self, emp):
        view_win = ctk.CTkToplevel(self)
        view_win.title(f"Hồ sơ: {emp[1]}")
        view_win.geometry("450x550")
        view_win.after(10, view_win.lift)
        view_win.grab_set()

        ctk.CTkLabel(view_win, text="CHI TIẾT NHÂN VIÊN", font=("Arial", 20, "bold"), text_color="#2563eb").pack(pady=25)
        
        container = ctk.CTkFrame(view_win, fg_color="white", corner_radius=15)
        container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        info = [
            ("Mã nhân viên", emp[1]), ("Họ và tên", emp[2]), ("Số điện thoại", emp[3]),
            ("Số CCCD", emp[4] or "Trống"), ("Email", emp[5] or "Trống"), ("Chức vụ", emp[6]),
            ("Phòng ban", emp[7]), ("Lương cơ bản", f"{int(emp[8]):,} VNĐ"),
            ("Ngày gia nhập", emp[9].strftime('%d/%m/%Y') if emp[9] else "N/A")
        ]

        for lbl, val in info:
            row = ctk.CTkFrame(container, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(row, text=f"{lbl}:", font=("Arial", 13, "bold"), text_color="#64748b", width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=("Arial", 13), text_color="#0f172a").pack(side="left")

        ctk.CTkButton(view_win, text="Đóng", command=view_win.destroy, fg_color="#94a3b8").pack(pady=20)

    def open_employee_modal(self, data=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Chỉnh sửa" if data else "Thêm nhân viên")
        modal.geometry("750x600")
        modal.after(10, modal.lift)
        modal.grab_set()

        ctk.CTkLabel(modal, text="THÔNG TIN HỒ SƠ NHÂN VIÊN", font=("Arial", 20, "bold")).pack(pady=20)

        main_container = ctk.CTkFrame(modal, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40)

        # Chia 2 cột
        left = ctk.CTkFrame(main_container, fg_color="transparent"); left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right = ctk.CTkFrame(main_container, fg_color="transparent"); right.pack(side="left", fill="both", expand=True)

        inputs = {}
        # Cột trái: Cá nhân
        for lbl, key, val in [("Họ và tên *", "name", 2), ("SĐT *", "phone", 3), ("CCCD *", "cccd", 4), ("Email", "email", 5)]:
            ctk.CTkLabel(left, text=lbl, text_color="#64748b").pack(anchor="w")
            e = ctk.CTkEntry(left, height=38); e.insert(0, str(data[val]) if data else ""); e.pack(fill="x", pady=(5, 15))
            inputs[key] = e

        # Cột phải: Công việc
        for lbl, key, val in [("Mã NV *", "code", 1), ("Chức vụ", "pos", 6), ("Lương *", "sal", 8)]:
            ctk.CTkLabel(right, text=lbl, text_color="#64748b").pack(anchor="w")
            e = ctk.CTkEntry(right, height=38); e.insert(0, str(data[val]) if data else ""); e.pack(fill="x", pady=(5, 15))
            inputs[key] = e

        ctk.CTkLabel(right, text="Phòng ban", text_color="#64748b").pack(anchor="w")
        dept_cb = ctk.CTkComboBox(right, height=38, values=["Kỹ thuật", "Kinh doanh", "Hành chính"])
        dept_cb.set(data[7] if data else "Kỹ thuật"); dept_cb.pack(fill="x", pady=(5, 15)); inputs['dept'] = dept_cb

        ctk.CTkLabel(right, text="Ngày gia nhập (YYYY-MM-DD)", text_color="#64748b").pack(anchor="w")
        date_e = ctk.CTkEntry(right, height=38)
        date_e.insert(0, data[9].strftime('%Y-%m-%d') if data and data[9] else datetime.now().strftime('%Y-%m-%d'))
        date_e.pack(fill="x", pady=5); inputs['date'] = date_e

        # --- NÚT XÁC NHẬN ---
        footer = ctk.CTkFrame(modal, fg_color="transparent")
        footer.pack(fill="x", pady=25, padx=40)
        ctk.CTkButton(footer, text="Hủy bỏ", width=120, height=42, fg_color="#94a3b8", command=modal.destroy).pack(side="left")
        btn_txt = "Lưu thay đổi" if data else "Xác nhận thêm mới"
        ctk.CTkButton(footer, text=btn_txt, width=220, height=42, fg_color="#2563eb", 
                      command=lambda: self.save_employee(inputs, modal, data[0] if data else None)).pack(side="right")

    def save_employee(self, f, win, emp_id):
        code, name, phone, cccd = f['code'].get().strip(), f['name'].get().strip(), f['phone'].get().strip(), f['cccd'].get().strip()
        if not (code and name and phone and cccd):
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng điền các trường có dấu *")
            return

        db = connect_db()
        if db:
            try:
                cursor = db.cursor()
                # KIỂM TRA TRÙNG LẶP
                check_sql = "SELECT employee_code, phone, cccd FROM employees WHERE (employee_code=%s OR phone=%s OR cccd=%s)"
                params = (code, phone, cccd)
                if emp_id: check_sql += " AND id != %s"; params += (emp_id,)
                
                cursor.execute(check_sql, params)
                exist = cursor.fetchone()
                if exist:
                    if exist[0] == code: m = "Mã NV đã tồn tại!"
                    elif exist[1] == phone: m = "SĐT đã được sử dụng!"
                    else: m = "CCCD đã tồn tại!"
                    messagebox.showerror("Lỗi trùng lặp", m); return

                vals = (code, name, phone, cccd, f['email'].get(), f['pos'].get(), f['dept'].get(), float(f['sal'].get() or 0), f['date'].get())
                if emp_id:
                    sql = "UPDATE employees SET employee_code=%s, full_name=%s, phone=%s, cccd=%s, email=%s, position=%s, department=%s, salary=%s, hire_date=%s WHERE id=%s"
                    cursor.execute(sql, vals + (emp_id,))
                else:
                    sql = "INSERT INTO employees (employee_code, full_name, phone, cccd, email, position, department, salary, hire_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(sql, vals)
                
                db.commit(); win.destroy(); self.load_employees()
                messagebox.showinfo("Thành công", "Đã lưu thông tin nhân viên!")
            except Exception as e: messagebox.showerror("Lỗi", f"Lỗi DB: {e}")
            finally: db.close()

    def delete_emp(self, id, name):
        if messagebox.askyesno("Xác nhận", f"Xóa nhân viên {name}?"):
            db = connect_db(); cursor = db.cursor()
            cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
            db.commit(); db.close(); self.load_employees()