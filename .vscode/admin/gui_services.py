import customtkinter as ctk
from database import connect_db
from tkinter import messagebox

# --- 1. CỬA SỔ THÊM/SỬA DỊCH VỤ ---
class ServiceFormWindow(ctk.CTkToplevel):
    def __init__(self, parent_frame, service_data=None):
        super().__init__()
        self.parent_frame = parent_frame
        # service_data[0] là 'id'
        self.service_id = service_data[0] if service_data else None
        
        self.title("Thêm dịch vụ mới" if not self.service_id else "Cập nhật dịch vụ")
        self.geometry("500x650")
        self.attributes("-topmost", True)
        self.configure(fg_color="white")

        title_text = "THÊM DỊCH VỤ MỚI" if not self.service_id else "CHỈNH SỬA DỊCH VỤ"
        ctk.CTkLabel(self, text=title_text, font=("Arial", 20, "bold"), text_color="#1e293b").pack(pady=25)

        # Các trường nhập liệu (Khớp với cấu trúc Database của Thao)
        self.ent_name = self.create_input("Tên dịch vụ *:", "VD: Thay nhớt động cơ")
        self.cbo_category = self.create_combo("Danh mục *:", ["Bảo dưỡng", "Sửa chữa", "Làm đẹp", "Thay thế phụ tùng", "Kiểm tra định kỳ"])
        self.txt_desc = self.create_textbox("Mô tả dịch vụ *:")
        self.ent_price = self.create_input("Giá dịch vụ (VNĐ) *:", "0")
        self.ent_duration = self.create_input("Thời gian dự kiến (phút) *:", "30")

        # Nếu là chế độ Sửa, đổ dữ liệu cũ vào form
        if service_data:
            # Thứ tự theo bảng: id(0), service_name(1), category(2), price(3), duration_min(4), description(5)
            self.ent_name.insert(0, service_data[1])
            self.cbo_category.set(service_data[2])
            self.ent_price.delete(0, "end")
            self.ent_price.insert(0, int(service_data[3])) # decimal sang int để hiển thị đẹp
            self.ent_duration.delete(0, "end")
            self.ent_duration.insert(0, service_data[4])
            self.txt_desc.insert("1.0", service_data[5] if service_data[5] else "")

        btn_color = "#2563eb" if not self.service_id else "#10b981"
        ctk.CTkButton(self, text="Lưu thông tin", fg_color=btn_color, height=45, 
                      font=("Arial", 14, "bold"), command=self.save_service).pack(pady=30, padx=50, fill="x")

    def create_input(self, label, placeholder):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=50, pady=5)
        ctk.CTkLabel(f, text=label, font=("Arial", 12, "bold")).pack(anchor="w")
        e = ctk.CTkEntry(f, height=35, placeholder_text=placeholder)
        e.pack(fill="x")
        return e

    def create_combo(self, label, values):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=50, pady=5)
        ctk.CTkLabel(f, text=label, font=("Arial", 12, "bold")).pack(anchor="w")
        c = ctk.CTkComboBox(f, values=values, height=35)
        c.pack(fill="x")
        return c

    def create_textbox(self, label):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=50, pady=5)
        ctk.CTkLabel(f, text=label, font=("Arial", 12, "bold")).pack(anchor="w")
        t = ctk.CTkTextbox(f, height=80, border_width=2, border_color="#e2e8f0")
        t.pack(fill="x")
        return t

    def save_service(self):
        name = self.ent_name.get().strip()
        cat = self.cbo_category.get()
        desc = self.txt_desc.get("1.0", "end-1c").strip()
        price = self.ent_price.get().strip()
        duration = self.ent_duration.get().strip()

        # Validation logic
        if not name or not price:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tên và Giá dịch vụ!")
            return
        
        if not price.isdigit():
            messagebox.showerror("Lỗi dữ liệu", "Giá tiền và thời gian phải là số!")
            return

        db = connect_db()
        if db:
            try:
                cursor = db.cursor()
                if self.service_id: # UPDATE: Khớp với tên cột service_name, duration_min
                    sql = """UPDATE services 
                             SET service_name=%s, category=%s, price=%s, duration_min=%s, description=%s 
                             WHERE id=%s"""
                    cursor.execute(sql, (name, cat, price, duration, desc, self.service_id))
                else: # INSERT: Khớp với tên cột service_name, duration_min
                    sql = """INSERT INTO services (service_name, category, price, duration_min, description) 
                             VALUES (%s, %s, %s, %s, %s)"""
                    cursor.execute(sql, (name, cat, price, duration, desc))
                
                db.commit()
                messagebox.showinfo("Thành công", "Đã cập nhật danh sách dịch vụ!")
                self.parent_frame.load_services()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi SQL", f"Không thể lưu: {e}")
            finally:
                db.close()

# --- 2. GIAO DIỆN CHÍNH QUẢN LÝ DỊCH VỤ ---
class ServiceFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        ctk.CTkLabel(header, text="Dịch vụ", font=("Arial", 26, "bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Thêm dịch vụ", fg_color="#2563eb", 
                      command=lambda: ServiceFormWindow(self)).pack(side="right")

        # Tìm kiếm
        search_f = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#e2e8f0")
        search_f.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))
        self.ent_search = ctk.CTkEntry(search_f, placeholder_text="🔍 Tìm kiếm dịch vụ...", 
                                       border_width=0, fg_color="transparent", height=45)
        self.ent_search.pack(fill="x", padx=10)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_services())

        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll_container.grid_columnconfigure((0, 1), weight=1)

        self.load_services()

    def load_services(self):
        for w in self.scroll_container.winfo_children(): w.destroy()
        
        db = connect_db()
        if db:
            cursor = db.cursor()
            search = f"%{self.ent_search.get()}%"
            # Sửa lỗi: dùng 'service_name' thay vì 'name'
            query = "SELECT * FROM services WHERE service_name LIKE %s OR category LIKE %s"
            cursor.execute(query, (search, search))
            services = cursor.fetchall()
            
            for i, s in enumerate(services):
                # s[0]:id, s[1]:service_name, s[2]:category, s[3]:price, s[4]:duration_min, s[5]:description
                card = ctk.CTkFrame(self.scroll_container, fg_color="white", corner_radius=12, 
                                    border_width=1, border_color="#e2e8f0")
                card.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")
                
                # Tên dịch vụ
                ctk.CTkLabel(card, text=s[1], font=("Arial", 16, "bold"), text_color="#1e293b").pack(anchor="w", padx=15, pady=(15, 0))
                
                # Tag danh mục
                tag_f = ctk.CTkFrame(card, fg_color="#f1f5f9", corner_radius=6)
                tag_f.pack(anchor="w", padx=15, pady=5)
                ctk.CTkLabel(tag_f, text=s[2], font=("Arial", 10, "bold"), text_color="#64748b").pack(padx=8, pady=2)

                # Mô tả (s[5])
                desc_text = s[5] if s[5] else "Không có mô tả."
                ctk.CTkLabel(card, text=desc_text, font=("Arial", 12), text_color="gray", wraplength=350, justify="left").pack(anchor="w", padx=15)
                
                # Giá (s[3])
                ctk.CTkLabel(card, text=f"{int(s[3]):,} VNĐ", font=("Arial", 18, "bold"), text_color="#2563eb").pack(anchor="w", padx=15, pady=(10, 0))
                
                # Thời gian (s[4])
                ctk.CTkLabel(card, text=f"⏱ Thời gian: {s[4]} phút", font=("Arial", 11), text_color="gray").pack(anchor="w", padx=15, pady=(0, 15))

                # Nút thao tác
                btn_f = ctk.CTkFrame(card, fg_color="transparent")
                btn_f.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
                ctk.CTkButton(btn_f, text="✎", width=30, fg_color="transparent", text_color="gray", 
                              command=lambda data=s: ServiceFormWindow(self, data)).pack(side="left")
                ctk.CTkButton(btn_f, text="🗑", width=30, fg_color="transparent", text_color="#ef4444", 
                              command=lambda sid=s[0]: self.delete_service(sid)).pack(side="left")
            db.close()

    def delete_service(self, sid):
        if messagebox.askyesno("Xác nhận", "Xóa dịch vụ này khỏi danh mục?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM services WHERE id=%s", (sid,))
                db.commit()
                db.close()
                self.load_services()