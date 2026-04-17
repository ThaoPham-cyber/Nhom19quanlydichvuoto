import customtkinter as ctk
from database import connect_db
from tkinter import messagebox

class CustomerDetailWindow(ctk.CTkToplevel):
    def __init__(self, customer_data):
        super().__init__()
        self.title("Chi tiết khách hàng")
        self.geometry("850x700")
        self.attributes("-topmost", True)
        self.configure(fg_color="#f8fafc")
        
        self.cust_id = customer_data[0]
        self.cust_name = customer_data[1]
        self.cust_phone = customer_data[2]
        self.cust_email = customer_data[3]

        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(self.main_scroll, text="CHI TIẾT KHÁCH HÀNG", font=("Arial", 22, "bold"), text_color="#1e293b").pack(anchor="w", pady=(0, 20))

        # Thông tin cá nhân
        info_card = ctk.CTkFrame(self.main_scroll, fg_color="white", corner_radius=15, border_width=1, border_color="#e2e8f0")
        info_card.pack(fill="x", pady=(0, 20))
        
        details = [
            ("Họ và tên", self.cust_name, 0, 0),
            ("Số điện thoại", f"📞 {self.cust_phone}", 0, 1),
            ("Email", f"✉ {self.cust_email}", 1, 0),
            ("Địa chỉ", "Chưa cập nhật", 1, 1)
        ]
        for label, val, r, c in details:
            container = ctk.CTkFrame(info_card, fg_color="transparent")
            container.grid(row=r, column=c, padx=20, pady=10, sticky="w")
            ctk.CTkLabel(container, text=label, font=("Arial", 11), text_color="#64748b").pack(anchor="w")
            ctk.CTkLabel(container, text=val, font=("Arial", 13, "bold")).pack(anchor="w")
        info_card.grid_columnconfigure((0, 1), weight=1)

        self.render_service_history()

    def render_service_history(self):
        ctk.CTkLabel(self.main_scroll, text="Lịch sử dịch vụ", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))
        db = connect_db()
        if db:
            cursor = db.cursor()
            # Truy vấn từ bảng service_history theo ID khách hàng
            query = "SELECT service_name, plate_number, service_date, price, status FROM service_history WHERE customer_id = %s ORDER BY service_date DESC"
            cursor.execute(query, (self.cust_id,))
            services = cursor.fetchall()
            if not services:
                ctk.CTkLabel(self.main_scroll, text="Chưa có lịch sử dịch vụ.", text_color="gray").pack(pady=20)
            else:
                for s in services:
                    card = ctk.CTkFrame(self.main_scroll, fg_color="white", corner_radius=12, border_width=1, border_color="#f1f5f9")
                    card.pack(fill="x", pady=5)
                    left_f = ctk.CTkFrame(card, fg_color="transparent")
                    left_f.pack(side="left", padx=15, pady=10)
                    ctk.CTkLabel(left_f, text=s[0], font=("Arial", 14, "bold")).pack(anchor="w")
                    ctk.CTkLabel(left_f, text=f"🚗 {s[1]}  •  📅 {s[2]}", font=("Arial", 11), text_color="gray").pack(anchor="w")
                    
                    right_f = ctk.CTkFrame(card, fg_color="transparent")
                    right_f.pack(side="right", padx=15, pady=10)
                    ctk.CTkLabel(right_f, text=f"{int(s[3]):,} đ", font=("Arial", 14, "bold"), text_color="#7c3aed").pack()
            db.close()

class CustomerWindow(ctk.CTkToplevel):
    def __init__(self, parent_frame, data=None):
        super().__init__()
        self.parent_frame = parent_frame
        self.customer_data = data
        self.title("Thông tin khách hàng")
        
        # Cố định kích thước cửa sổ đủ lớn để hiện nút
        self.geometry("450x620") 
        self.attributes("-topmost", True)
        self.configure(fg_color="white")
        self.resizable(False, False)

        title_text = "CẬP NHẬT KHÁCH HÀNG" if data else "THÊM KHÁCH HÀNG"
        ctk.CTkLabel(self, text=title_text, font=("Arial", 22, "bold"), text_color="#1e293b").pack(pady=(35, 25))

        # Khung nhập liệu
        input_container = ctk.CTkFrame(self, fg_color="transparent")
        input_container.pack(fill="x", padx=45)

        self.ent_name = self.create_input(input_container, "Họ và tên:", data[1] if data else "")
        self.ent_phone = self.create_input(input_container, "Số điện thoại:", data[2] if data else "")
        self.ent_email = self.create_input(input_container, "Email:", data[3] if data else "")

        # Nút bấm chính
        btn_color = "#10b981" if data else "#2563eb"
        btn_text = "Xác nhận cập nhật" if data else "Lưu thông tin"
        
        self.btn_save = ctk.CTkButton(
            self, 
            text=btn_text, 
            fg_color=btn_color, 
            hover_color="#059669" if data else "#1d4ed8",
            height=48, 
            font=("Arial", 14, "bold"),
            command=self.save_data
        )
        self.btn_save.pack(pady=(40, 20), padx=45, fill="x")

    def create_input(self, master, label, value):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(fill="x", pady=12)
        ctk.CTkLabel(frame, text=label, font=("Arial", 13, "bold"), text_color="#475569").pack(anchor="w", pady=(0, 5))
        entry = ctk.CTkEntry(frame, height=42, corner_radius=8, border_color="#e2e8f0", fg_color="#f8fafc")
        entry.pack(fill="x")
        if value:
            entry.insert(0, value)
        return entry

    def save_data(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()

        if not name or not phone:
            messagebox.showwarning("Lỗi", "Vui lòng nhập đầy đủ Tên và SĐT!")
            return
        
        # Hỏi xác nhận trước khi sửa
        if self.customer_data:
            if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn cập nhật thay đổi này?"):
                return

        db = connect_db()
        if db:
            cursor = db.cursor()
            try:
                if self.customer_data:
                    sql = "UPDATE customers SET full_name=%s, phone=%s, email=%s WHERE id=%s"
                    cursor.execute(sql, (name, phone, email, self.customer_data[0]))
                else:
                    sql = "INSERT INTO customers (full_name, phone, email, visit_count) VALUES (%s, %s, %s, 0)"
                    cursor.execute(sql, (name, phone, email))
                db.commit()
                self.parent_frame.load_data()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu: {e}")
            finally:
                db.close()

class CustomerFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc", corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=25)
        ctk.CTkLabel(header, text="Quản lý khách hàng", font=("Arial", 28, "bold"), text_color="#1e293b").pack(side="left")
        ctk.CTkButton(header, text="+ Thêm mới", fg_color="#2563eb", font=("Arial", 13, "bold"), height=40, command=lambda: CustomerWindow(self)).pack(side="right")

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12, height=55, border_width=1, border_color="#e2e8f0")
        search_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 25))
        search_frame.pack_propagate(False)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Tìm kiếm theo tên hoặc số điện thoại...", border_width=0, fg_color="transparent", font=("Arial", 14))
        self.search_entry.pack(fill="both", expand=True, padx=20)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_data())

        # Table container
        self.table_container = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=15, border_width=1, border_color="#e2e8f0")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        # Cấu hình tỉ lệ cột cho bảng khách hàng
        self.table_container.grid_columnconfigure(0, weight=3) # Tên
        self.table_container.grid_columnconfigure(1, weight=2) # SĐT
        self.table_container.grid_columnconfigure(2, weight=3) # Email
        self.table_container.grid_columnconfigure(3, weight=1) # Lượt sửa
        self.table_container.grid_columnconfigure(4, weight=1) # Thao tác

        self.load_data()

    def load_data(self):
        if not hasattr(self, 'search_entry'): return
        
        for w in self.table_container.winfo_children(): w.destroy()
        
        # Render tiêu đề cột
        headers = [("Tên khách hàng", "w"), ("Số điện thoại", "w"), ("Email", "w"), ("Số lần sửa", "w"), ("Thao tác", "e")]
        for i, (text, align) in enumerate(headers):
            ctk.CTkLabel(self.table_container, text=text, font=("Arial", 12, "bold"), text_color="#64748b").grid(row=0, column=i, pady=15, padx=20, sticky=align)

        search_val = self.search_entry.get()
        db = connect_db()
        if db:
            cursor = db.cursor()
            query = "SELECT id, full_name, phone, email, visit_count FROM customers WHERE full_name LIKE %s OR phone LIKE %s ORDER BY id DESC"
            cursor.execute(query, (f"%{search_val}%", f"%{search_val}%"))
            results = cursor.fetchall()
            
            for i, row in enumerate(results, start=1):
                # Đường kẻ ngang giữa các dòng
                ctk.CTkFrame(self.table_container, height=1, fg_color="#f1f5f9").grid(row=i, column=0, columnspan=5, sticky="ew")
                
                ctk.CTkLabel(self.table_container, text=row[1], font=("Arial", 14, "bold"), text_color="#1e293b").grid(row=i, column=0, padx=20, pady=20, sticky="w")
                ctk.CTkLabel(self.table_container, text=f"📞 {row[2]}", font=("Arial", 13)).grid(row=i, column=1, padx=20, sticky="w")
                ctk.CTkLabel(self.table_container, text=row[3] if row[3] else "N/A", font=("Arial", 13)).grid(row=i, column=2, padx=20, sticky="w")
                ctk.CTkLabel(self.table_container, text=f"{row[4]} lần", text_color="#2563eb", font=("Arial", 13, "bold")).grid(row=i, column=3, padx=20, sticky="w")
                
                # Nút thao tác căn lề phải
                btn_frame = ctk.CTkFrame(self.table_container, fg_color="transparent")
                btn_frame.grid(row=i, column=4, padx=20, sticky="e")
                
                ctk.CTkButton(btn_frame, text="👁", width=32, height=32, fg_color="transparent", text_color="#3b82f6", font=("Arial", 16), command=lambda r=row: CustomerDetailWindow(r)).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="✎", width=32, height=32, fg_color="transparent", text_color="#64748b", font=("Arial", 16), command=lambda r=row: CustomerWindow(self, r)).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="🗑", width=32, height=32, fg_color="transparent", text_color="#ef4444", font=("Arial", 16), command=lambda id=row[0]: self.delete_customer(id)).pack(side="left", padx=2)
            db.close()

    def delete_customer(self, customer_id):
        if messagebox.askyesno("Xác nhận", "Hành động này sẽ xóa vĩnh viễn khách hàng này. Bạn có chắc không?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                try:
                    cursor.execute("DELETE FROM customers WHERE id=%s", (customer_id,))
                    db.commit()
                    self.load_data()
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể xóa: {e}")
                finally:
                    db.close()