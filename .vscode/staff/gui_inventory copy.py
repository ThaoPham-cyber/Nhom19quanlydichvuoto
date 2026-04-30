import customtkinter as ctk
from database import connect_db
from tkinter import messagebox

class InventoryFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) 

        # --- 1. Header Area ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=35, pady=(25, 5))
        
        ctk.CTkLabel(header, text="Quản lý kho hàng", font=("Arial", 28, "bold"), text_color="#0f172a").pack(side="left")
        
        btn_add = ctk.CTkButton(header, text="+ Thêm hàng hóa", fg_color="#2563eb", hover_color="#1d4ed8",
                                font=("Arial", 13, "bold"), height=40, corner_radius=8,
                                command=self.open_add_modal)
        btn_add.pack(side="right")

        # --- 2. Search Bar ---
        search_f = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#e2e8f0")
        search_f.grid(row=1, column=0, sticky="ew", padx=35, pady=(0, 15))
        
        self.ent_search = ctk.CTkEntry(search_f, placeholder_text="🔍 Tìm kiếm theo mã, tên, hãng...", 
                                       border_width=0, fg_color="transparent", height=45)
        self.ent_search.pack(fill="x", padx=10)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_inventory())

        # --- 3. Alert Banner ---
        self.alert_f = ctk.CTkFrame(self, fg_color="transparent")
        self.alert_f.grid(row=2, column=0, sticky="w", padx=35, pady=(0, 10))
        self.alert_icon = ctk.CTkLabel(self.alert_f, text="", text_color="#f97316", font=("Arial", 14))
        self.alert_icon.pack(side="left")
        self.alert_label = ctk.CTkLabel(self.alert_f, text="", text_color="#f97316", font=("Arial", 13))
        self.alert_label.pack(side="left", padx=5)

        # --- 4. Main Table ---
        self.table_container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        self.table_container.grid(row=3, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        self.create_table_header()

        self.scroll_data = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent", corner_radius=0)
        self.scroll_data.pack(fill="both", expand=True, padx=5, pady=5)
        self.scroll_data.grid_columnconfigure((0,1,2,3,4,5), weight=2)
        self.scroll_data.grid_columnconfigure(6, weight=1)

        self.load_inventory()

    def create_table_header(self):
        header_table = ctk.CTkFrame(self.table_container, fg_color="transparent", height=50)
        header_table.pack(fill="x", padx=20, pady=(10, 0))
        header_table.grid_columnconfigure((0,1,2,3,4,5), weight=2)
        header_table.grid_columnconfigure(6, weight=1)
        
        headers = ["Mã hàng", "Tên hàng", "Danh mục", "Tồn kho", "Giá", "Vị trí", "Thao tác"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(header_table, text=text, font=("Arial", 12, "bold"), text_color="#64748b").grid(row=0, column=col, sticky="w", padx=10)

    def load_inventory(self):
        for w in self.scroll_data.winfo_children(): w.destroy()
        db = connect_db()
        if db:
            cursor = db.cursor()
            search_val = f"%{self.ent_search.get()}%"
            query = "SELECT * FROM inventory WHERE product_code LIKE %s OR product_name LIKE %s"
            cursor.execute(query, (search_val, search_val))
            items = cursor.fetchall()
            
            low_stock_count = 0
            for i, row in enumerate(items):
                is_low = row[5] <= row[6] 
                if is_low: low_stock_count += 1
                
                ctk.CTkLabel(self.scroll_data, text=row[1], font=("Arial", 12)).grid(row=i*2, column=0, sticky="w", padx=20, pady=12)
                
                name_color = "#f97316" if is_low else "#1e293b"
                prefix = "⚠️ " if is_low else ""
                ctk.CTkLabel(self.scroll_data, text=f"{prefix}{row[2]}", font=("Arial", 13, "bold"), text_color=name_color).grid(row=i*2, column=1, sticky="w", padx=10)
                
                tag_bg = "#eff6ff" if row[3] == "Phụ tùng" else "#f5f3ff"
                tag_fg = "#2563eb" if row[3] == "Phụ tùng" else "#7c3aed"
                ctk.CTkLabel(self.scroll_data, text=row[3], font=("Arial", 10, "bold"), fg_color=tag_bg, text_color=tag_fg, corner_radius=6, width=80, height=26).grid(row=i*2, column=2, sticky="w", padx=10)
                
                stock_f = ctk.CTkFrame(self.scroll_data, fg_color="transparent")
                stock_f.grid(row=i*2, column=3, sticky="w", padx=10)
                ctk.CTkLabel(stock_f, text=f"{row[5]} {row[7]}", font=("Arial", 12, "bold")).pack(anchor="w")
                ctk.CTkLabel(stock_f, text=f"Tối thiểu: {row[6]}", font=("Arial", 10), text_color="#94a3b8").pack(anchor="w")
                
                ctk.CTkLabel(self.scroll_data, text=f"{int(row[8]):,}đ", font=("Arial", 13, "bold")).grid(row=i*2, column=4, sticky="w", padx=10)
                ctk.CTkLabel(self.scroll_data, text=row[9], font=("Arial", 12), text_color="#64748b").grid(row=i*2, column=5, sticky="w", padx=10)
                
                btn_f = ctk.CTkFrame(self.scroll_data, fg_color="transparent")
                btn_f.grid(row=i*2, column=6, sticky="w", padx=(10, 0))
                ctk.CTkButton(btn_f, text="✎", width=32, height=32, corner_radius=6, fg_color="#f1f5f9", text_color="#64748b",
                               command=lambda r=row: self.open_edit_modal(r)).pack(side="left", padx=(0, 8))
                ctk.CTkButton(btn_f, text="🗑", width=32, height=32, corner_radius=6, fg_color="#fff1f2", text_color="#ef4444",
                               command=lambda r=row: self.delete_item(r[0], r[2])).pack(side="left")

                ctk.CTkFrame(self.scroll_data, height=1, fg_color="#f1f5f9").grid(row=i*2+1, column=0, columnspan=7, sticky="ew", pady=(5, 0))

            if low_stock_count > 0:
                self.alert_label.configure(text=f"{low_stock_count} mặt hàng sắp hết hoặc dưới mức tối thiểu")
                self.alert_icon.configure(text="⚠️")
            else:
                self.alert_label.configure(text="")
                self.alert_icon.configure(text="")
            db.close()

    def open_add_modal(self):
        # FORM THÊM MỚI ĐẦY ĐỦ TRƯỜNG
        modal = ctk.CTkToplevel(self)
        modal.title("Thêm hàng hóa mới")
        modal.geometry("850x680")
        modal.after(10, modal.lift)
        modal.grab_set()

        ctk.CTkLabel(modal, text="Thêm hàng hóa mới", font=("Arial", 22, "bold")).pack(pady=(25, 20))
        form_f = ctk.CTkFrame(modal, fg_color="transparent")
        form_f.pack(fill="both", expand=True, padx=45)
        form_f.grid_columnconfigure((0, 1), weight=1)

        # Hàng 1: Mã & Danh mục
        ctk.CTkLabel(form_f, text="Mã hàng *").grid(row=0, column=0, sticky="w")
        ent_code = ctk.CTkEntry(form_f, placeholder_text="VD: NK001", height=40)
        ent_code.grid(row=1, column=0, sticky="ew", padx=(0, 15), pady=(5, 15))

        ctk.CTkLabel(form_f, text="Danh mục *").grid(row=0, column=1, sticky="w")
        cb_cat = ctk.CTkComboBox(form_f, values=["Phụ tùng", "Phụ kiện"], height=40)
        cb_cat.grid(row=1, column=1, sticky="ew", pady=(5, 15))

        # Hàng 2: Tên hàng hóa
        ctk.CTkLabel(form_f, text="Tên hàng hóa *").grid(row=2, column=0, columnspan=2, sticky="w")
        ent_name = ctk.CTkEntry(form_f, placeholder_text="Nhập tên hàng hóa", height=40)
        ent_name.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 15))

        # Hàng 3: Hãng & Đơn vị
        ctk.CTkLabel(form_f, text="Hãng/Thương hiệu *").grid(row=4, column=0, sticky="w")
        ent_brand = ctk.CTkEntry(form_f, placeholder_text="VD: Castrol, Denso", height=40)
        ent_brand.grid(row=5, column=0, sticky="ew", padx=(0, 15), pady=(5, 15))

        ctk.CTkLabel(form_f, text="Đơn vị tính *").grid(row=4, column=1, sticky="w")
        cb_unit = ctk.CTkComboBox(form_f, values=["Lít", "Cái", "Bộ", "Chai"], height=40)
        cb_unit.grid(row=5, column=1, sticky="ew", pady=(5, 15))

        # Hàng 4: Tồn kho & Tối thiểu
        ctk.CTkLabel(form_f, text="Số lượng tồn kho *").grid(row=6, column=0, sticky="w")
        ent_stock = ctk.CTkEntry(form_f, height=40)
        ent_stock.insert(0, "0")
        ent_stock.grid(row=7, column=0, sticky="ew", padx=(0, 15), pady=(5, 15))

        ctk.CTkLabel(form_f, text="Số lượng tối thiểu *").grid(row=6, column=1, sticky="w")
        ent_min = ctk.CTkEntry(form_f, height=40)
        ent_min.insert(0, "0")
        ent_min.grid(row=7, column=1, sticky="ew", pady=(5, 15))

        # Hàng 5: Giá & Vị trí
        ctk.CTkLabel(form_f, text="Giá (VNĐ) *").grid(row=8, column=0, sticky="w")
        ent_price = ctk.CTkEntry(form_f, height=40)
        ent_price.insert(0, "0")
        ent_price.grid(row=9, column=0, sticky="ew", padx=(0, 15), pady=(5, 15))

        ctk.CTkLabel(form_f, text="Vị trí trong kho").grid(row=8, column=1, sticky="w")
        ent_loc = ctk.CTkEntry(form_f, placeholder_text="VD: Kệ A1", height=40)
        ent_loc.grid(row=9, column=1, sticky="ew", pady=(5, 15))

        btn_f = ctk.CTkFrame(modal, fg_color="transparent")
        btn_f.pack(fill="x", pady=25, padx=45)
        
        ctk.CTkButton(btn_f, text="Thêm mới", fg_color="#2563eb", height=45, width=140, 
                      command=lambda: self.save_item(ent_code.get(), ent_name.get(), cb_cat.get(), 
                                                   ent_brand.get(), ent_stock.get(), ent_min.get(), 
                                                   cb_unit.get(), ent_price.get(), ent_loc.get(), modal)).pack(side="right")
        ctk.CTkButton(btn_f, text="Hủy", fg_color="transparent", text_color="#64748b", height=45, width=100, command=modal.destroy).pack(side="right", padx=15)

    def save_item(self, code, name, cat, brand, stock, min_s, unit, price, loc, window):
        if not all([code, name, brand]):
            messagebox.showerror("Lỗi", "Vui lòng điền đủ thông tin *")
            return
        db = connect_db()
        if db:
            cursor = db.cursor()
            try:
                sql = """INSERT INTO inventory (product_code, product_name, category, brand, stock_quantity, min_stock, unit, price, location) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (code, name, cat, brand, int(stock), int(min_s), unit, float(price), loc))
                db.commit()
                messagebox.showinfo("Thành công", "Đã thêm hàng hóa!")
                window.destroy()
                self.load_inventory()
            except Exception as e: messagebox.showerror("Lỗi", f"Lỗi: {e}")
            finally: db.close()

    def open_edit_modal(self, row):
        # FORM SỬA ĐẦY ĐỦ TRƯỜNG
        modal = ctk.CTkToplevel(self)
        modal.title(f"Sửa: {row[2]}")
        modal.geometry("850x680")
        modal.after(10, modal.lift)
        modal.grab_set()

        ctk.CTkLabel(modal, text="Chỉnh sửa thông tin", font=("Arial", 22, "bold")).pack(pady=20)
        form_f = ctk.CTkFrame(modal, fg_color="transparent")
        form_f.pack(fill="both", expand=True, padx=45)
        form_f.grid_columnconfigure((0, 1), weight=1)

        # Tạo lại các ô nhập và INSERT DỮ LIỆU CŨ
        ctk.CTkLabel(form_f, text="Mã hàng *").grid(row=0, column=0, sticky="w")
        ent_code = ctk.CTkEntry(form_f, height=40); ent_code.insert(0, row[1])
        ent_code.grid(row=1, column=0, sticky="ew", padx=(0, 15), pady=10)

        ctk.CTkLabel(form_f, text="Danh mục *").grid(row=0, column=1, sticky="w")
        cb_cat = ctk.CTkComboBox(form_f, values=["Phụ tùng", "Phụ kiện"], height=40); cb_cat.set(row[3])
        cb_cat.grid(row=1, column=1, sticky="ew", pady=10)

        ctk.CTkLabel(form_f, text="Tên hàng hóa *").grid(row=2, column=0, columnspan=2, sticky="w")
        ent_name = ctk.CTkEntry(form_f, height=40); ent_name.insert(0, row[2])
        ent_name.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        ctk.CTkLabel(form_f, text="Hãng *").grid(row=4, column=0, sticky="w")
        ent_brand = ctk.CTkEntry(form_f, height=40); ent_brand.insert(0, row[4])
        ent_brand.grid(row=5, column=0, sticky="ew", padx=(0, 15), pady=10)

        ctk.CTkLabel(form_f, text="Đơn vị tính *").grid(row=4, column=1, sticky="w")
        cb_unit = ctk.CTkComboBox(form_f, values=["Lít", "Cái", "Bộ", "Chai"], height=40); cb_unit.set(row[7])
        cb_unit.grid(row=5, column=1, sticky="ew", pady=10)

        ctk.CTkLabel(form_f, text="Tồn kho *").grid(row=6, column=0, sticky="w")
        ent_stock = ctk.CTkEntry(form_f, height=40); ent_stock.insert(0, str(row[5]))
        ent_stock.grid(row=7, column=0, sticky="ew", padx=(0, 15), pady=10)

        ctk.CTkLabel(form_f, text="Giá *").grid(row=6, column=1, sticky="w")
        ent_price = ctk.CTkEntry(form_f, height=40); ent_price.insert(0, str(int(row[8])))
        ent_price.grid(row=7, column=1, sticky="ew", pady=10)

        btn_save = ctk.CTkButton(modal, text="Lưu thay đổi", fg_color="#2563eb", height=45, width=150,
                                 command=lambda: self.update_item(row[0], ent_code.get(), ent_name.get(), cb_cat.get(),
                                                                ent_brand.get(), ent_stock.get(), cb_unit.get(), ent_price.get(), modal))
        btn_save.pack(pady=20)

    def update_item(self, item_id, code, name, cat, brand, stock, unit, price, window):
        db = connect_db()
        if db:
            cursor = db.cursor()
            try:
                sql = """UPDATE inventory SET product_code=%s, product_name=%s, category=%s, brand=%s, 
                         stock_quantity=%s, unit=%s, price=%s WHERE id=%s"""
                cursor.execute(sql, (code, name, cat, brand, int(stock), unit, float(price), item_id))
                db.commit()
                messagebox.showinfo("Thành công", "Đã cập nhật!")
                window.destroy()
                self.load_inventory()
            finally: db.close()

    def delete_item(self, item_id, item_name):
        if messagebox.askyesno("Xác nhận", f"Xóa '{item_name}'?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
                db.commit(); db.close()
                self.load_inventory()