import customtkinter as ctk
from database import connect_db
from tkinter import messagebox
from datetime import datetime

# --- 1. CỬA SỔ XEM CHI TIẾT ---
class CarDetailWindow(ctk.CTkToplevel):
    def __init__(self, plate_number):
        super().__init__()
        self.title(f"Chi tiết xe: {plate_number}")
        self.geometry("700x650")
        self.attributes("-topmost", True)
        self.configure(fg_color="#f8fafc")

        ctk.CTkLabel(self, text=f"THÔNG TIN CHI TIẾT XE {plate_number}", 
                     font=("Arial", 22, "bold"), text_color="#1e293b").pack(pady=20)

        db = connect_db()
        if db:
            cursor = db.cursor()
            query = """
                SELECT c.plate_number, c.brand, c.model, c.year, cust.full_name, cust.phone, cust.email
                FROM cars c
                JOIN customers cust ON c.customer_id = cust.id
                WHERE c.plate_number = %s
            """
            cursor.execute(query, (plate_number,))
            data = cursor.fetchone()
            cursor.close()
            db.close()

            if data:
                info_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15, border_width=1, border_color="#e2e8f0")
                info_frame.pack(padx=30, pady=10, fill="x")
                info_frame.grid_columnconfigure((0, 2), weight=1) 
                info_frame.grid_columnconfigure((1, 3), weight=2) 

                fields = [
                    ("Biển số:", data[0]), ("Hãng xe:", data[1]), 
                    ("Mẫu xe:", data[2]), ("Năm SX:", data[3]),
                    ("Chủ xe:", data[4]), ("SĐT:", data[5]),
                    ("Email:", data[6] if data[6] else "Chưa có")
                ]

                for i, (label, value) in enumerate(fields):
                    row = i // 2
                    col_label = (i % 2) * 2
                    col_val = col_label + 1
                    ctk.CTkLabel(info_frame, text=label, font=("Arial", 12, "bold"), text_color="gray").grid(row=row, column=col_label, padx=10, pady=15, sticky="e")
                    ctk.CTkLabel(info_frame, text=value, font=("Arial", 13, "bold"), text_color="#1e293b").grid(row=row, column=col_val, padx=10, pady=15, sticky="w")

        history_frame = ctk.CTkScrollableFrame(self, fg_color="white", height=300, corner_radius=10)
        history_frame.pack(padx=30, fill="both", expand=True, pady=20)
        ctk.CTkLabel(history_frame, text="Lịch sử dịch vụ bảo dưỡng sẽ hiển thị tại đây.", text_color="gray").pack(pady=50)

# --- 2. CỬA SỔ SỬA THÔNG TIN XE ---
class EditCarWindow(ctk.CTkToplevel):
    def __init__(self, parent_frame, plate_number):
        super().__init__()
        self.parent_frame = parent_frame
        self.old_plate = plate_number
        self.geometry("450x550")
        self.title("Sửa thông tin xe")
        self.attributes("-topmost", True)
        self.configure(fg_color="white")

        ctk.CTkLabel(self, text="CẬP NHẬT THÔNG TIN", font=("Arial", 18, "bold")).pack(pady=20)

        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT brand, model, year FROM cars WHERE plate_number=%s", (plate_number,))
        curr = cursor.fetchone()
        cursor.close()
        db.close()

        self.ent_brand = self.create_input("Hãng xe:", curr[0])
        self.ent_model = self.create_input("Mẫu xe:", curr[1])
        self.ent_year = self.create_input("Năm sản xuất:", curr[2])

        ctk.CTkButton(self, text="Lưu thay đổi", fg_color="#10b981", height=40, command=self.update_data).pack(pady=30, padx=50, fill="x")

    def create_input(self, label, value):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=50, pady=5)
        ctk.CTkLabel(f, text=label).pack(anchor="w")
        e = ctk.CTkEntry(f, height=35)
        e.insert(0, value)
        e.pack(fill="x")
        return e

    def update_data(self):
        year_str = self.ent_year.get().strip()
        current_year = datetime.now().year
        
        # Kiểm tra năm sản xuất khi sửa
        if not year_str.isdigit() or int(year_str) > current_year:
            messagebox.showerror("Lỗi", f"Năm sản xuất không hợp lệ (không được lớn hơn {current_year})!")
            return

        db = connect_db()
        cursor = db.cursor()
        cursor.execute("UPDATE cars SET brand=%s, model=%s, year=%s WHERE plate_number=%s", 
                       (self.ent_brand.get(), self.ent_model.get(), year_str, self.old_plate))
        db.commit()
        db.close()
        self.parent_frame.load_data()
        self.destroy()

# --- 3. CỬA SỔ THÊM XE MỚI (Có kiểm tra điều kiện) ---
class AddCarWindow(ctk.CTkToplevel):
    def __init__(self, parent_frame):
        super().__init__()
        self.parent_frame = parent_frame
        self.title("Thêm xe mới")
        self.geometry("500x700")
        self.attributes("-topmost", True)
        self.configure(fg_color="white")

        ctk.CTkLabel(self, text="THÊM XE & CHỦ XE", font=("Arial", 20, "bold")).pack(pady=20)

        self.ent_plate = self.create_input("Biển số xe *:", "30A-123.45")
        self.ent_brand = self.create_input("Hãng xe:", "Toyota")
        self.ent_model = self.create_input("Mẫu xe:", "Vios")
        self.ent_year = self.create_input("Năm sản xuất:", "2024")
        
        ctk.CTkLabel(self, text="--- Thông tin chủ xe ---", font=("Arial", 13, "italic"), text_color="gray").pack(pady=5)
        self.ent_owner = self.create_input("Họ tên chủ xe *:", "Tên khách hàng")
        self.ent_phone = self.create_input("Số điện thoại *:", "Nhập đủ 10 số")
        self.ent_email = self.create_input("Email:", "phải có ký tự @")

        ctk.CTkButton(self, text="Lưu thông tin", fg_color="#2563eb", height=45, 
                      font=("Arial", 14, "bold"), command=self.save_data).pack(pady=30, padx=50, fill="x")

    def create_input(self, label, placeholder):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=50, pady=5)
        ctk.CTkLabel(f, text=label, font=("Arial", 12, "bold")).pack(anchor="w")
        e = ctk.CTkEntry(f, height=35, placeholder_text=placeholder)
        e.pack(fill="x")
        return e

    def save_data(self):
        plate = self.ent_plate.get().strip()
        phone = self.ent_phone.get().strip()
        name = self.ent_owner.get().strip()
        email = self.ent_email.get().strip()
        year_str = self.ent_year.get().strip()
        current_year = datetime.now().year
        
        # 1. Kiểm tra rỗng
        if not plate or not phone or not name:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập Biển số, Tên và SĐT!")
            return

        # 2. KIỂM TRA SĐT (Phải là 10 số)
        if not (phone.isdigit() and len(phone) == 10):
            messagebox.showerror("Lỗi SĐT", "Số điện thoại phải bao gồm đúng 10 chữ số!")
            return

        # 3. KIỂM TRA EMAIL (Nếu có nhập thì phải có @)
        if email and "@" not in email:
            messagebox.showerror("Lỗi Email", "Email không hợp lệ (phải có ký tự '@')!")
            return

        # 4. KIỂM TRA NĂM SẢN XUẤT (Không lớn hơn năm hiện tại)
        if year_str:
            if not year_str.isdigit() or int(year_str) > current_year:
                messagebox.showerror("Lỗi Năm", f"Năm sản xuất không hợp lệ (không được lớn hơn {current_year})!")
                return

        db = connect_db()
        if db:
            try:
                cursor = db.cursor()
                cursor.execute("SELECT id FROM customers WHERE phone = %s", (phone,))
                res = cursor.fetchone()
                
                if res:
                    cust_id = res[0]
                    cursor.execute("UPDATE customers SET email = %s, visit_count = visit_count + 1 WHERE id = %s", (email, cust_id))
                else:
                    cursor.execute("INSERT INTO customers (full_name, phone, email, visit_count) VALUES (%s, %s, %s, 1)", 
                                   (name, phone, email))
                    cust_id = cursor.lastrowid

                cursor.execute("INSERT INTO cars (plate_number, brand, model, year, customer_id) VALUES (%s, %s, %s, %s, %s)",
                               (plate, self.ent_brand.get(), self.ent_model.get(), year_str, cust_id))
                
                db.commit()
                messagebox.showinfo("Thành công", "Đã lưu xe thành công!")
                self.parent_frame.load_data()
                self.destroy()
            except Exception as e:
                db.rollback()
                messagebox.showerror("Lỗi SQL", f"Lỗi: {e}")
            finally:
                cursor.close()
                db.close()

# --- 4. TRANG CHÍNH QUẢN LÝ XE ---
class CarFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        ctk.CTkLabel(header, text="Quản lý xe", font=("Arial", 26, "bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Thêm xe mới", fg_color="#2563eb", command=lambda: AddCarWindow(self)).pack(side="right")

        search_f = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#e2e8f0")
        search_f.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))
        self.ent_search = ctk.CTkEntry(search_f, placeholder_text="🔍 Tìm kiếm biển số xe...", border_width=0, fg_color="transparent", height=40)
        self.ent_search.pack(fill="x", padx=10)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_data())

        self.table_container = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=15, border_width=1, border_color="#e2e8f0")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.table_container.grid_columnconfigure((0,1,2,3,4), weight=1)

        self.load_data()

    def load_data(self):
        for w in self.table_container.winfo_children(): w.destroy()
        headers = ["Biển số", "Hãng xe", "Mẫu xe", "Chủ xe", "Thao tác"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.table_container, text=h, font=("Arial", 12, "bold"), text_color="gray").grid(row=0, column=i, pady=10)

        db = connect_db()
        if db:
            cursor = db.cursor()
            search = f"%{self.ent_search.get()}%"
            query = """
                SELECT c.plate_number, c.brand, c.model, cust.full_name 
                FROM cars c
                JOIN customers cust ON c.customer_id = cust.id
                WHERE c.plate_number LIKE %s
            """
            cursor.execute(query, (search,))
            for i, row in enumerate(cursor.fetchall(), start=1):
                ctk.CTkLabel(self.table_container, text=row[0], font=("Arial", 13, "bold"), text_color="#2563eb").grid(row=i, column=0, pady=12)
                ctk.CTkLabel(self.table_container, text=row[1]).grid(row=i, column=1, pady=12)
                ctk.CTkLabel(self.table_container, text=row[2]).grid(row=i, column=2, pady=12)
                ctk.CTkLabel(self.table_container, text=row[3]).grid(row=i, column=3, pady=12)
                
                btn_f = ctk.CTkFrame(self.table_container, fg_color="transparent")
                btn_f.grid(row=i, column=4)
                ctk.CTkButton(btn_f, text="👁", width=30, fg_color="transparent", text_color="#3b82f6", command=lambda p=row[0]: CarDetailWindow(p)).pack(side="left")
                ctk.CTkButton(btn_f, text="✎", width=30, fg_color="transparent", text_color="#64748b", command=lambda p=row[0]: EditCarWindow(self, p)).pack(side="left")
                ctk.CTkButton(btn_f, text="🗑", width=30, fg_color="transparent", text_color="red", command=lambda p=row[0]: self.delete_car(p)).pack(side="left")
            cursor.close()
            db.close()

    def delete_car(self, plate):
        if messagebox.askyesno("Xác nhận", f"Xóa xe {plate}?"):
            db = connect_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM cars WHERE plate_number=%s", (plate,))
            db.commit()
            cursor.close()
            db.close()
            self.load_data()