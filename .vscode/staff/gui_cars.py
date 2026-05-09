import customtkinter as ctk
from database import connect_db
from tkinter import messagebox
from datetime import datetime


class CarDetailWindow(ctk.CTkToplevel):
    def __init__(self, plate_number):
        super().__init__()
        self.title(f"Chi tiết xe: {plate_number}")
        self.geometry("800x700")
        self.attributes("-topmost", True)
        self.configure(fg_color="#f8fafc")

        ctk.CTkLabel(self, text=f"THÔNG TIN CHI TIẾT XE {plate_number}", 
                     font=("Arial", 22, "bold"), text_color="#1e293b").pack(pady=20)

        db = connect_db()
        if db:
            cursor = db.cursor()
            query = """
                SELECT c.plate_number, c.brand, c.model, c.year, 
                       cust.full_name, cust.phone, cust.email, cust.address,
                       c.last_service
                FROM cars c
                JOIN customers cust ON c.customer_id = cust.id
                WHERE c.plate_number = %s
            """
            cursor.execute(query, (plate_number,))
            data = cursor.fetchone()
            cursor.close()
            db.close()

            if data:
                # Car info card
                info_card = ctk.CTkFrame(self, fg_color="white", corner_radius=15, 
                                        border_width=1, border_color="#e2e8f0")
                info_card.pack(padx=30, pady=10, fill="x")
                
                ctk.CTkLabel(info_card, text="THÔNG TIN XE", font=("Arial", 16, "bold"),
                            text_color="#2563eb").pack(anchor="w", padx=20, pady=(15, 10))
                
                fields_car = [
                    ("Biển số:", data[0]), 
                    ("Hãng xe:", data[1] or "Chưa cập nhật"),
                    ("Mẫu xe:", data[2] or "Chưa cập nhật"), 
                    ("Năm SX:", data[3] if data[3] else "Chưa cập nhật"),
                    ("Lần bảo dưỡng cuối:", data[8] if data[8] else "Chưa có")
                ]
                
                for label, value in fields_car:
                    row_frame = ctk.CTkFrame(info_card, fg_color="transparent")
                    row_frame.pack(fill="x", padx=20, pady=5)
                    ctk.CTkLabel(row_frame, text=label, width=140, font=("Arial", 12, "bold"),
                                text_color="#64748b").pack(side="left")
                    ctk.CTkLabel(row_frame, text=value, font=("Arial", 13)).pack(side="left", padx=(10, 0))
                
                # Customer info card
                cust_card = ctk.CTkFrame(self, fg_color="white", corner_radius=15,
                                        border_width=1, border_color="#e2e8f0")
                cust_card.pack(padx=30, pady=10, fill="x")
                
                ctk.CTkLabel(cust_card, text="THÔNG TIN CHỦ XE", font=("Arial", 16, "bold"),
                            text_color="#2563eb").pack(anchor="w", padx=20, pady=(15, 10))
                
                fields_cust = [
                    ("Chủ xe:", data[4]), 
                    ("SĐT:", data[5]),
                    ("Email:", data[6] if data[6] else "Chưa có"), 
                    ("Địa chỉ:", data[7] if data[7] else "Chưa có")
                ]
                
                for label, value in fields_cust:
                    row_frame = ctk.CTkFrame(cust_card, fg_color="transparent")
                    row_frame.pack(fill="x", padx=20, pady=5)
                    ctk.CTkLabel(row_frame, text=label, width=140, font=("Arial", 12, "bold"),
                                text_color="#64748b").pack(side="left")
                    ctk.CTkLabel(row_frame, text=value, font=("Arial", 13)).pack(side="left", padx=(10, 0))
        
        # Service history
        history_frame = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=15,
                                               height=300)
        history_frame.pack(padx=30, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(history_frame, text="LỊCH SỬ DỊCH VỤ", font=("Arial", 16, "bold"),
                    text_color="#2563eb").pack(anchor="w", padx=15, pady=(15, 10))
        
        db2 = connect_db()
        if db2:
            cursor2 = db2.cursor()
            cursor2.execute("""
                SELECT service_name, service_date, service_time, price, status
                FROM service_history
                WHERE plate_number = %s
                ORDER BY service_date DESC
            """, (plate_number,))
            histories = cursor2.fetchall()
            
            if histories:
                for h in histories:
                    hist_card = ctk.CTkFrame(history_frame, fg_color="#f8fafc", corner_radius=10)
                    hist_card.pack(fill="x", padx=15, pady=5)
                    
                    left = ctk.CTkFrame(hist_card, fg_color="transparent")
                    left.pack(side="left", padx=15, pady=10, fill="both", expand=True)
                    
                    ctk.CTkLabel(left, text=h[0], font=("Arial", 14, "bold")).pack(anchor="w")
                    date_str = h[1].strftime("%d/%m/%Y") if h[1] else ""
                    time_str = str(h[2]) if h[2] else ""
                    ctk.CTkLabel(left, text=f"📅 {date_str} • 🕐 {time_str}", 
                                font=("Arial", 11), text_color="#64748b").pack(anchor="w")
                    
                    right = ctk.CTkFrame(hist_card, fg_color="transparent")
                    right.pack(side="right", padx=15, pady=10)
                    
                    ctk.CTkLabel(right, text=f"{int(h[3]):,} ₫" if h[3] else "0 ₫",
                                font=("Arial", 14, "bold"), text_color="#10b981").pack(anchor="e")
            else:
                ctk.CTkLabel(history_frame, text="Chưa có lịch sử dịch vụ", 
                            text_color="#94a3b8").pack(pady=30)
            db2.close()


class EditCarWindow(ctk.CTkToplevel):
    def __init__(self, parent_frame, plate_number):
        super().__init__()
        self.parent_frame = parent_frame
        self.old_plate = plate_number
        self.geometry("500x650")
        self.title("Sửa thông tin xe")
        self.attributes("-topmost", True)
        self.configure(fg_color="white")

        ctk.CTkLabel(self, text="CẬP NHẬT THÔNG TIN XE", font=("Arial", 20, "bold"),
                    text_color="#1e293b").pack(pady=20)

        db = connect_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT c.brand, c.model, c.year, cust.full_name, cust.phone, cust.email, cust.id
            FROM cars c
            JOIN customers cust ON c.customer_id = cust.id
            WHERE c.plate_number = %s
        """, (plate_number,))
        curr = cursor.fetchone()
        cursor.close()
        db.close()

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=40, pady=10)

        self.ent_brand = self.create_input(form_frame, "Hãng xe:", curr[0] if curr[0] else "")
        self.ent_model = self.create_input(form_frame, "Mẫu xe:", curr[1] if curr[1] else "")
        self.ent_year = self.create_input(form_frame, "Năm sản xuất:", curr[2] if curr[2] else "")
        
        ctk.CTkLabel(form_frame, text="--- Thông tin chủ xe ---", 
                    font=("Arial", 12, "italic"), text_color="#64748b").pack(pady=(15, 5))
        
        self.ent_owner = self.create_input(form_frame, "Họ tên chủ xe:", curr[3])
        self.ent_phone = self.create_input(form_frame, "Số điện thoại:", curr[4])
        self.ent_email = self.create_input(form_frame, "Email:", curr[5] if curr[5] else "")
        
        self.cust_id = curr[6]

        ctk.CTkButton(self, text="Lưu thay đổi", fg_color="#10b981", height=45,
                     font=("Arial", 14, "bold"), command=self.update_data).pack(pady=20, padx=50, fill="x")

    def create_input(self, parent, label, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        ctk.CTkLabel(frame, text=label, font=("Arial", 12, "bold"),
                    text_color="#475569").pack(anchor="w")
        entry = ctk.CTkEntry(frame, height=40, font=("Arial", 13))
        if value:
            entry.insert(0, value)
        entry.pack(fill="x", pady=(5, 0))
        return entry

    def update_data(self):
        current_year = datetime.now().year
        year_str = self.ent_year.get().strip()
        
        if year_str and (not year_str.isdigit() or int(year_str) > current_year):
            messagebox.showerror("Lỗi", f"Năm sản xuất không hợp lệ!")
            return
        
        phone = self.ent_phone.get().strip()
        if len(phone) < 9:
            messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ!")
            return

        db = connect_db()
        cursor = db.cursor()
        
        try:
            # Update customer info
            cursor.execute("""
                UPDATE customers 
                SET full_name=%s, phone=%s, email=%s 
                WHERE id=%s
            """, (self.ent_owner.get(), phone, self.ent_email.get(), self.cust_id))
            
            # Update car info
            cursor.execute("""
                UPDATE cars 
                SET brand=%s, model=%s, year=%s 
                WHERE plate_number=%s
            """, (self.ent_brand.get(), self.ent_model.get(), year_str, self.old_plate))
            
            db.commit()
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin xe!")
            self.parent_frame.load_data()
            self.destroy()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", str(e))
        finally:
            db.close()


class AddCarWindow(ctk.CTkToplevel):
    def __init__(self, parent_frame):
        super().__init__()
        self.parent_frame = parent_frame
        self.title("Thêm xe mới")
        self.geometry("550x750")
        self.attributes("-topmost", True)
        self.configure(fg_color="white")

        ctk.CTkLabel(self, text="THÊM XE VÀO HỆ THỐNG", font=("Arial", 22, "bold"),
                    text_color="#1e293b").pack(pady=25)

        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=40, pady=10)

        self.ent_plate = self.create_input(scroll_frame, "Biển số xe *:", "30A-123.45", True)
        self.ent_brand = self.create_input(scroll_frame, "Hãng xe:", "Toyota")
        self.ent_model = self.create_input(scroll_frame, "Mẫu xe:", "Vios")
        self.ent_year = self.create_input(scroll_frame, "Năm sản xuất:", str(datetime.now().year))
        
        ctk.CTkLabel(scroll_frame, text="--- Thông tin chủ xe ---", 
                    font=("Arial", 13, "italic"), text_color="#2563eb").pack(pady=(15, 5))
        
        self.ent_owner = self.create_input(scroll_frame, "Họ tên chủ xe *:", "Nguyễn Văn A", True)
        self.ent_phone = self.create_input(scroll_frame, "Số điện thoại *:", "0912345678", True)
        self.ent_email = self.create_input(scroll_frame, "Email:", "example@email.com")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkButton(btn_frame, text="Hủy", fg_color="transparent", text_color="#64748b",
                     height=45, command=self.destroy).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Lưu thông tin", fg_color="#2563eb", height=45,
                     font=("Arial", 14, "bold"), command=self.save_data).pack(side="right", fill="x", expand=True, padx=5)

    def create_input(self, parent, label, placeholder, required=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        label_text = label + " *" if required else label
        ctk.CTkLabel(frame, text=label_text, font=("Arial", 12, "bold"),
                    text_color="#ef4444" if required else "#475569").pack(anchor="w")
        
        entry = ctk.CTkEntry(frame, height=42, font=("Arial", 13))
        entry.insert(0, str(placeholder))
        entry.pack(fill="x", pady=(5, 0))
        return entry

    def save_data(self):
        plate = self.ent_plate.get().strip().upper()
        phone = self.ent_phone.get().strip()
        name = self.ent_owner.get().strip()
        email = self.ent_email.get().strip()
        year_str = self.ent_year.get().strip()
        
        if not all([plate, phone, name]):
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập đầy đủ thông tin bắt buộc (*)!")
            return
        
        if not phone.isdigit() or len(phone) < 9:
            messagebox.showerror("Lỗi SĐT", "Số điện thoại không hợp lệ!")
            return
        
        if email and "@" not in email:
            messagebox.showerror("Lỗi Email", "Email không hợp lệ!")
            return
        
        current_year = datetime.now().year
        if year_str and (not year_str.isdigit() or int(year_str) > current_year):
            messagebox.showerror("Lỗi Năm", f"Năm sản xuất không hợp lệ!")
            return

        db = connect_db()
        if db:
            cursor = db.cursor()
            try:
                # Check existing customer
                cursor.execute("SELECT id FROM customers WHERE phone = %s", (phone,))
                res = cursor.fetchone()
                
                if res:
                    cust_id = res[0]
                    cursor.execute("""
                        UPDATE customers 
                        SET full_name = %s, email = %s, visit_count = visit_count + 1 
                        WHERE id = %s
                    """, (name, email, cust_id))
                else:
                    cursor.execute("""
                        INSERT INTO customers (full_name, phone, email, visit_count) 
                        VALUES (%s, %s, %s, 1)
                    """, (name, phone, email))
                    cust_id = cursor.lastrowid
                
                # Check existing car
                cursor.execute("SELECT plate_number FROM cars WHERE plate_number = %s", (plate,))
                if cursor.fetchone():
                    messagebox.showerror("Lỗi", f"Biển số {plate} đã tồn tại!")
                    return
                
                cursor.execute("""
                    INSERT INTO cars (plate_number, brand, model, year, customer_id) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (plate, self.ent_brand.get(), self.ent_model.get(), year_str, cust_id))
                
                db.commit()
                messagebox.showinfo("Thành công", f"Đã thêm xe {plate} thành công!")
                self.parent_frame.load_data()
                self.destroy()
            except Exception as e:
                db.rollback()
                messagebox.showerror("Lỗi", str(e))
            finally:
                db.close()


class CarFrame(ctk.CTkFrame):
    """Trang quản lý xe chính"""
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        
        ctk.CTkLabel(header, text="Quản lý xe", font=("Arial", 28, "bold"),
                    text_color="#1e293b").pack(side="left")
        

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12, 
                                   border_width=1, border_color="#e2e8f0")
        search_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Tìm kiếm theo biển số xe...",
                                        border_width=0, fg_color="transparent", height=45)
        self.search_entry.pack(fill="x", padx=15)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_data())

        # Table container
        self.table_container = ctk.CTkFrame(self, fg_color="white", corner_radius=15,
                                           border_width=1, border_color="#e2e8f0")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        self.create_table_header()
        
        # Scrollable data area
        self.scroll_data = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent", 
                                                   corner_radius=0)
        self.scroll_data.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure columns
        for i in range(5):
            self.scroll_data.grid_columnconfigure(i, weight=1)
        
        self.load_data()

    def create_table_header(self):
        header_frame = ctk.CTkFrame(self.table_container, fg_color="transparent", height=50)
        header_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        headers = ["Biển số", "Hãng xe", "Mẫu xe", "Chủ xe", "Thao tác"]
        for i, text in enumerate(headers):
            ctk.CTkLabel(header_frame, text=text, font=("Arial", 12, "bold"),
                        text_color="#64748b").grid(row=0, column=i, padx=10, pady=10, sticky="w")

    def load_data(self):
        # Clear existing data
        for w in self.scroll_data.winfo_children():
            w.destroy()
        
        db = connect_db()
        if not db:
            return
        
        cursor = db.cursor()
        search = f"%{self.search_entry.get()}%"
        
        query = """
            SELECT c.plate_number, c.brand, c.model, cust.full_name, cust.id
            FROM cars c
            JOIN customers cust ON c.customer_id = cust.id
            WHERE c.plate_number LIKE %s
            ORDER BY c.plate_number
        """
        cursor.execute(query, (search,))
        cars = cursor.fetchall()
        
        for idx, car in enumerate(cars):
            row_idx = idx * 2
            
            # Biển số
            ctk.CTkLabel(self.scroll_data, text=car[0], font=("Arial", 14, "bold"),
                        text_color="#2563eb").grid(row=row_idx, column=0, padx=10, pady=12, sticky="w")
            
            # Hãng xe
            brand_text = car[1] if car[1] else "—"
            ctk.CTkLabel(self.scroll_data, text=brand_text, font=("Arial", 13)).grid(row=row_idx, column=1, padx=10, pady=12, sticky="w")
            
            # Mẫu xe
            model_text = car[2] if car[2] else "—"
            ctk.CTkLabel(self.scroll_data, text=model_text, font=("Arial", 13)).grid(row=row_idx, column=2, padx=10, pady=12, sticky="w")
            
            # Chủ xe
            ctk.CTkLabel(self.scroll_data, text=car[3], font=("Arial", 13)).grid(row=row_idx, column=3, padx=10, pady=12, sticky="w")
            
            # Action buttons
            btn_frame = ctk.CTkFrame(self.scroll_data, fg_color="transparent")
            btn_frame.grid(row=row_idx, column=4, padx=10, pady=12)
            
            ctk.CTkButton(btn_frame, text="👁", width=35, height=32, corner_radius=6,
                        fg_color="transparent", text_color="#3b82f6", font=("Arial", 14),
                        command=lambda p=car[0]: CarDetailWindow(p)).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="✎", width=35, height=32, corner_radius=6,
                        fg_color="transparent", text_color="#64748b", font=("Arial", 14),
                        command=lambda p=car[0]: EditCarWindow(self, p)).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="🗑", width=35, height=32, corner_radius=6,
                        fg_color="transparent", text_color="#ef4444", font=("Arial", 14),
                        command=lambda p=car[0]: self.delete_car(p)).pack(side="left", padx=2)
            
            # Separator line
            ctk.CTkFrame(self.scroll_data, height=1, fg_color="#f1f5f9").grid(row=row_idx+1, column=0, columnspan=5, sticky="ew")
        
        cursor.close()
        db.close()

    def delete_car(self, plate_number):
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa xe {plate_number} không?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                try:
                    cursor.execute("DELETE FROM cars WHERE plate_number = %s", (plate_number,))
                    db.commit()
                    messagebox.showinfo("Thành công", f"Đã xóa xe {plate_number}")
                    self.load_data()
                except Exception as e:
                    db.rollback()
                    messagebox.showerror("Lỗi", f"Không thể xóa: {e}")
                finally:
                    cursor.close()
                    db.close()