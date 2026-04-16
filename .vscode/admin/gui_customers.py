import customtkinter as ctk
from database import connect_db
from tkinter import messagebox

class CustomerDetailWindow(ctk.CTkToplevel):
    """Cửa sổ hiển thị chi tiết thông tin và lịch sử dịch vụ của khách hàng"""
    def __init__(self, customer_data):
        super().__init__()
        self.title("Chi tiết khách hàng")
        self.geometry("850x700")
        self.attributes("-topmost", True)
        self.configure(fg_color="#f8fafc")
        
        # Dữ liệu khách hàng từ row: (id, name, phone, email, visit_count)
        self.cust_id = customer_data[0]
        self.cust_name = customer_data[1]
        self.cust_phone = customer_data[2]
        self.cust_email = customer_data[3]

        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        self.render_header()
        self.render_personal_info()
        self.render_service_history()

    def render_header(self):
        header_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="CHI TIẾT KHÁCH HÀNG", font=("Arial", 22, "bold"), text_color="#1e293b").pack(side="left")

    def render_personal_info(self):
        info_card = ctk.CTkFrame(self.main_scroll, fg_color="white", corner_radius=15, border_width=1, border_color="#e2e8f0")
        info_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(info_card, text="Thông tin cá nhân", font=("Arial", 16, "bold"), text_color="#1e293b").grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        details = [
            ("Họ và tên", self.cust_name, 1, 0),
            ("Số điện thoại", f"📞 {self.cust_phone}", 1, 1),
            ("Email", f"✉ {self.cust_email}", 2, 0),
            ("Địa chỉ", "Chưa cập nhật", 2, 1)
        ]
        
        for label, val, r, c in details:
            container = ctk.CTkFrame(info_card, fg_color="transparent")
            container.grid(row=r, column=c, padx=20, pady=10, sticky="w")
            ctk.CTkLabel(container, text=label, font=("Arial", 11), text_color="#64748b").pack(anchor="w")
            ctk.CTkLabel(container, text=val, font=("Arial", 13, "bold"), text_color="#1e293b").pack(anchor="w")
        
        info_card.grid_columnconfigure((0, 1), weight=1)

    def render_service_history(self):
        ctk.CTkLabel(self.main_scroll, text="Lịch sử dịch vụ", font=("Arial", 16, "bold"), text_color="#1e293b").pack(anchor="w", pady=(10, 10))
        
        db = connect_db()
        if db:
            cursor = db.cursor()
            # Thao cần đảm bảo bảng service_history có dữ liệu hoặc thay bằng bảng appointments của bạn
            query = "SELECT service_name, plate_number, service_date, price, status FROM service_history WHERE customer_id = %s ORDER BY service_date DESC"
            try:
                cursor.execute(query, (self.cust_id,))
                services = cursor.fetchall()
                
                if not services:
                    ctk.CTkLabel(self.main_scroll, text="Chưa có lịch sử dịch vụ.", font=("Arial", 12, "italic"), text_color="gray").pack(pady=20)
                
                for s in services:
                    card = ctk.CTkFrame(self.main_scroll, fg_color="white", corner_radius=12, border_width=1, border_color="#f1f5f9")
                    card.pack(fill="x", pady=5)
                    
                    # Cột trái: Tên dịch vụ & Biển số
                    left_f = ctk.CTkFrame(card, fg_color="transparent")
                    left_f.pack(side="left", padx=15, pady=10)
                    ctk.CTkLabel(left_f, text=s[0], font=("Arial", 14, "bold"), text_color="#1e293b").pack(anchor="w")
                    ctk.CTkLabel(left_f, text=f"🚗 {s[1]}  •  📅 {s[2]}", font=("Arial", 11), text_color="gray").pack(anchor="w")
                    
                    # Cột phải: Giá & Trạng thái
                    right_f = ctk.CTkFrame(card, fg_color="transparent")
                    right_f.pack(side="right", padx=15, pady=10)
                    
                    status_colors = {"Hoàn thành": "#dcfce7", "Đang sửa": "#dbeafe", "Chờ xác nhận": "#fef9c3"}
                    text_colors = {"Hoàn thành": "#166534", "Đang sửa": "#1e40af", "Chờ xác nhận": "#854d0e"}
                    
                    st_lbl = ctk.CTkLabel(right_f, text=s[4], fg_color=status_colors.get(s[4], "#f1f5f9"), 
                                          text_color=text_colors.get(s[4], "black"), corner_radius=8, width=100, font=("Arial", 11, "bold"))
                    st_lbl.pack(pady=(0, 5))
                    ctk.CTkLabel(right_f, text=f"{int(s[3]):,} đ", font=("Arial", 14, "bold"), text_color="#7c3aed").pack()
            except:
                ctk.CTkLabel(self.main_scroll, text="Lỗi: Bảng service_history chưa được tạo.", text_color="red").pack()
            finally:
                db.close()

class CustomerWindow(ctk.CTkToplevel):
    def __init__(self, parent_frame, data=None):
        super().__init__()
        self.parent_frame = parent_frame
        self.customer_data = data
        self.title("Thông tin khách hàng")
        self.geometry("400x550")
        self.attributes("-topmost", True)
        self.configure(fg_color="white")

        title_text = "CẬP NHẬT KHÁCH HÀNG" if data else "THÊM KHÁCH HÀNG"
        ctk.CTkLabel(self, text=title_text, font=("Arial", 20, "bold"), text_color="#1e293b").pack(pady=25)

        self.ent_name = self.create_input("Họ và tên:", data[1] if data else "")
        self.ent_phone = self.create_input("Số điện thoại:", data[2] if data else "")
        self.ent_email = self.create_input("Email:", data[3] if data else "")

        btn_color = "#10b981" if data else "#2563eb"
        ctk.CTkButton(self, text="Lưu thông tin", fg_color=btn_color, height=45, 
                      font=("Arial", 14, "bold"), command=self.save_data).pack(pady=30, padx=40, fill="x")

    def create_input(self, label, value):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=40, pady=5)
        ctk.CTkLabel(frame, text=label, font=("Arial", 12, "bold"), text_color="#64748b").pack(anchor="w")
        entry = ctk.CTkEntry(frame, height=38, corner_radius=8)
        entry.pack(fill="x", pady=5)
        entry.insert(0, value)
        return entry

    def save_data(self):
        name, phone, email = self.ent_name.get(), self.ent_phone.get(), self.ent_email.get()
        if not name or not phone:
            messagebox.showwarning("Lỗi", "Vui lòng nhập Tên và SĐT!")
            return
        db = connect_db()
        if db:
            cursor = db.cursor()
            try:
                if self.customer_data:
                    sql = "UPDATE customers SET full_name=%s, phone=%s, email=%s WHERE id=%s"
                    cursor.execute(sql, (name, phone, email, self.customer_data[0]))
                else:
                    # Khi thêm khách mới, mặc định số lần đến là 0 (hoặc 1 tùy Thao)
                    sql = "INSERT INTO customers (full_name, phone, email, visit_count) VALUES (%s, %s, %s, 0)"
                    cursor.execute(sql, (name, phone, email))
                db.commit()
                self.parent_frame.load_data()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi SQL: {e}")
            finally:
                db.close()

class CustomerFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc", corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        ctk.CTkLabel(header, text="Quản lý khách hàng", font=("Arial", 28, "bold"), text_color="#1e293b").pack(side="left")
        ctk.CTkButton(header, text="+ Thêm mới", fg_color="#2563eb", font=("Arial", 13, "bold"), 
                      height=38, command=lambda: CustomerWindow(self)).pack(side="right")

        # Search Bar
        search_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10, height=50, border_width=1, border_color="#e2e8f0")
        search_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))
        search_frame.pack_propagate(False)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Tìm kiếm khách hàng theo tên hoặc số điện thoại...", border_width=0, fg_color="transparent", font=("Arial", 14))
        self.search_entry.pack(fill="both", expand=True, padx=15)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_data())

        # Table
        self.table_container = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=15, border_width=1, border_color="#e2e8f0")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        # Căn tỷ lệ cột
        self.table_container.grid_columnconfigure(0, weight=3, uniform="col")
        self.table_container.grid_columnconfigure(1, weight=2, uniform="col")
        self.table_container.grid_columnconfigure(2, weight=3, uniform="col")
        self.table_container.grid_columnconfigure(3, weight=2, uniform="col")
        self.table_container.grid_columnconfigure(4, weight=2, uniform="col")

        self.load_data()

    def load_data(self):
        for w in self.table_container.winfo_children(): w.destroy()
        
        headers = ["Tên khách hàng", "Số điện thoại", "Email", "Số lần sửa", "Thao tác"]
        for i, text in enumerate(headers):
            ctk.CTkLabel(self.table_container, text=text, font=("Arial", 12, "bold"), 
                         text_color="#64748b").grid(row=0, column=i, pady=10, padx=15, sticky="w")

        search_val = self.search_entry.get()
        db = connect_db()
        if db:
            cursor = db.cursor()
            # Lấy visit_count trực tiếp từ DB
            query = """
                SELECT id, full_name, phone, email, visit_count 
                FROM customers 
                WHERE full_name LIKE %s OR phone LIKE %s
                ORDER BY id DESC
            """
            cursor.execute(query, (f"%{search_val}%", f"%{search_val}%"))
            results = cursor.fetchall()
            
            for i, row in enumerate(results, start=1):
                # Line separator
                ctk.CTkFrame(self.table_container, height=1, fg_color="#f1f5f9").grid(row=i, column=0, columnspan=5, sticky="ew")

                # Name
                ctk.CTkLabel(self.table_container, text=row[1], font=("Arial", 14, "bold"), text_color="#1e293b").grid(row=i, column=0, padx=15, pady=18, sticky="w")
                
                # Phone
                p_f = ctk.CTkFrame(self.table_container, fg_color="transparent")
                p_f.grid(row=i, column=1, padx=15, sticky="w")
                ctk.CTkLabel(p_f, text="📞", font=("Arial", 15)).pack(side="left", padx=(0,5))
                ctk.CTkLabel(p_f, text=row[2], font=("Arial", 13)).pack(side="left")
                
                # Email
                e_f = ctk.CTkFrame(self.table_container, fg_color="transparent")
                e_f.grid(row=i, column=2, padx=15, sticky="w")
                ctk.CTkLabel(e_f, text="✉", font=("Arial", 18)).pack(side="left", padx=(0,5))
                ctk.CTkLabel(e_f, text=row[3], font=("Arial", 13)).pack(side="left")
                
                # Visit Count (Cột Số lần sửa)
                ctk.CTkLabel(self.table_container, text=f"{row[4]} lần", font=("Arial", 13, "bold"), text_color="#2563eb").grid(row=i, column=3, padx=15, sticky="w")
                
                # Actions (View, Edit, Delete)
                btn_frame = ctk.CTkFrame(self.table_container, fg_color="transparent")
                btn_frame.grid(row=i, column=4, padx=15)
                
                # View 👁️
                ctk.CTkButton(btn_frame, text="👁", width=32, height=32, fg_color="transparent", text_color="#3b82f6", font=("Arial", 18), hover_color="#eff6ff", command=lambda r=row: CustomerDetailWindow(r)).pack(side="left", padx=2)
                # Edit ✎
                ctk.CTkButton(btn_frame, text="✎", width=32, height=32, fg_color="transparent", text_color="#64748b", font=("Arial", 18), hover_color="#f1f5f9", command=lambda r=row: CustomerWindow(self, r)).pack(side="left", padx=2)
                # Delete 🗑
                ctk.CTkButton(btn_frame, text="🗑", width=32, height=32, fg_color="transparent", text_color="#ef4444", font=("Arial", 18), hover_color="#fee2e2", command=lambda id=row[0]: self.delete_customer(id)).pack(side="left", padx=2)

            db.close()

    def delete_customer(self, customer_id):
        if messagebox.askyesno("Xác nhận", "Hành động này sẽ xóa vĩnh viễn khách hàng. Bạn có chắc chắn?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                try:
                    cursor.execute("DELETE FROM customers WHERE id=%s", (customer_id,))
                    db.commit()
                    self.load_data()
                except Exception as e:
                    messagebox.showerror("Lỗi", "Không thể xóa khách hàng đang có lịch sử sửa chữa!")
                finally:
                    db.close()