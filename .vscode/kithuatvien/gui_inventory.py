import customtkinter as ctk
from database import connect_db
from tkinter import messagebox


class InventoryFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=35, pady=(25, 5))
        
        ctk.CTkLabel(header, text="Quản lý kho hàng", font=("Arial", 28, "bold"), text_color="#0f172a").pack(side="left")
        
        btn_add = ctk.CTkButton(header, text="+ Thêm hàng hóa", fg_color="#2563eb", hover_color="#1d4ed8",
                                font=("Arial", 13, "bold"), height=40, corner_radius=8,
                                command=self.open_add_modal)
        btn_add.pack(side="right")
        
        btn_link = ctk.CTkButton(header, text="🔗 Liên kết dịch vụ", fg_color="#8b5cf6", hover_color="#7c3aed",
                                font=("Arial", 13, "bold"), height=40, corner_radius=8,
                                command=self.open_service_link_window)
        btn_link.pack(side="right", padx=5)

        # Search
        search_f = ctk.CTkFrame(self, fg_color="white", corner_radius=10, border_width=1, border_color="#e2e8f0")
        search_f.grid(row=1, column=0, sticky="ew", padx=35, pady=(0, 15))
        
        self.ent_search = ctk.CTkEntry(search_f, placeholder_text="🔍 Tìm kiếm theo mã, tên, hãng...", 
                                       border_width=0, fg_color="transparent", height=45)
        self.ent_search.pack(fill="x", padx=10)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_inventory())

        # Alert Banner
        self.alert_f = ctk.CTkFrame(self, fg_color="transparent")
        self.alert_f.grid(row=2, column=0, sticky="w", padx=35, pady=(0, 10))
        self.alert_icon = ctk.CTkLabel(self.alert_f, text="", text_color="#f97316", font=("Arial", 14))
        self.alert_icon.pack(side="left")
        self.alert_label = ctk.CTkLabel(self.alert_f, text="", text_color="#f97316", font=("Arial", 13))
        self.alert_label.pack(side="left", padx=5)

        # Main Table
        self.table_container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        self.table_container.grid(row=3, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        self.scroll_data = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent", corner_radius=0)
        self.scroll_data.pack(fill="both", expand=True, padx=5, pady=5)
        self.scroll_data.grid_columnconfigure((0,1,2,3,4,5,6), weight=2)
        self.scroll_data.grid_columnconfigure(7, weight=1)

        self.create_table_header()
        self.load_inventory()

    def create_table_header(self):
        headers = ["Mã hàng", "Tên hàng", "Danh mục", "Tồn kho", "Giá", "Vị trí", "Liên kết", "Thao tác"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(self.scroll_data, text=text, font=("Arial", 12, "bold"), text_color="#64748b").grid(row=0, column=col, sticky="ew", padx=10, pady=(10, 10))
        ctk.CTkFrame(self.scroll_data, height=1, fg_color="#e2e8f0").grid(row=1, column=0, columnspan=8, sticky="ew", padx=10, pady=(0, 5))

    def load_inventory(self):
        for w in self.scroll_data.winfo_children():
            info = w.grid_info()
            if info and info.get("row", 0) > 1:
                w.destroy()
        
        db = connect_db()
        if not db:
            return
            
        cursor = db.cursor()
        search_val = f"%{self.ent_search.get()}%"
        query = "SELECT * FROM inventory WHERE product_code LIKE %s OR product_name LIKE %s"
        cursor.execute(query, (search_val, search_val))
        items = cursor.fetchall()
        
        low_stock_count = 0
        for i, row in enumerate(items):
            is_low = row[5] <= row[6]
            if is_low:
                low_stock_count += 1
            
            row_idx = i * 2 + 2
            ctk.CTkLabel(self.scroll_data, text=row[1], font=("Arial", 12)).grid(row=row_idx, column=0, sticky="w", padx=20, pady=12)
            
            name_color = "#f97316" if is_low else "#1e293b"
            prefix = "⚠️ " if is_low else ""
            ctk.CTkLabel(self.scroll_data, text=f"{prefix}{row[2]}", font=("Arial", 13, "bold"), text_color=name_color).grid(row=row_idx, column=1, sticky="ew", padx=10)
            
            tag_bg = "#eff6ff" if row[3] == "Phụ tùng" else "#f5f3ff"
            tag_fg = "#2563eb" if row[3] == "Phụ tùng" else "#7c3aed"
            ctk.CTkLabel(self.scroll_data, text=row[3], font=("Arial", 10, "bold"), fg_color=tag_bg, text_color=tag_fg, corner_radius=6, width=80, height=26).grid(row=row_idx, column=2, sticky="ew", padx=10)
            
            stock_f = ctk.CTkFrame(self.scroll_data, fg_color="transparent")
            stock_f.grid(row=row_idx, column=3, sticky="ew", padx=10)
            ctk.CTkLabel(stock_f, text=f"{row[5]} {row[7]}", font=("Arial", 12, "bold")).pack(anchor="w")
            ctk.CTkLabel(stock_f, text=f"Tối thiểu: {row[6]}", font=("Arial", 10), text_color="#94a3b8").pack(anchor="w")
            
            ctk.CTkLabel(self.scroll_data, text=f"{int(row[8]):,}đ", font=("Arial", 13, "bold")).grid(row=row_idx, column=4, sticky="ew", padx=10)
            ctk.CTkLabel(self.scroll_data, text=row[9] if row[9] else "---", font=("Arial", 12), text_color="#64748b").grid(row=row_idx, column=5, sticky="ew", padx=10)
            
            # Lấy liên kết dịch vụ
            cursor.execute("""
                SELECT s.service_name 
                FROM service_products sp
                JOIN services s ON sp.service_id = s.id
                WHERE sp.product_id = %s
            """, (row[0],))
            linked_services = cursor.fetchall()
            link_text = ", ".join([ls[0] for ls in linked_services]) if linked_services else "Chưa liên kết"
            link_color = "#10b981" if linked_services else "#64748b"
            ctk.CTkLabel(self.scroll_data, text=link_text[:30], font=("Arial", 11), text_color=link_color).grid(row=row_idx, column=6, sticky="ew", padx=10)
            
            btn_f = ctk.CTkFrame(self.scroll_data, fg_color="transparent")
            btn_f.grid(row=row_idx, column=7, sticky="ew", padx=(10, 0))
            ctk.CTkButton(btn_f, text="✎", width=32, height=32, corner_radius=6, fg_color="#f1f5f9", text_color="#64748b",
                          command=lambda r=row: self.open_edit_modal(r)).pack(side="left", padx=(0, 8))
            ctk.CTkButton(btn_f, text="🗑", width=32, height=32, corner_radius=6, fg_color="#fff1f2", text_color="#ef4444",
                          command=lambda r=row: self.delete_item(r[0], r[2])).pack(side="left")

            ctk.CTkFrame(self.scroll_data, height=1, fg_color="#f1f5f9").grid(row=row_idx+1, column=0, columnspan=8, sticky="ew", pady=(5, 0))

        if low_stock_count > 0:
            self.alert_label.configure(text=f"{low_stock_count} mặt hàng sắp hết hoặc dưới mức tối thiểu")
            self.alert_icon.configure(text="⚠️")
        else:
            self.alert_label.configure(text="")
            self.alert_icon.configure(text="")
        
        cursor.close()
        db.close()

    def open_service_link_window(self):
        """Mở cửa sổ liên kết dịch vụ với vật tư - thiết kế mới"""
        link_window = ctk.CTkToplevel(self)
        link_window.title("Liên kết dịch vụ với vật tư")
        link_window.geometry("1100x700")
        link_window.attributes("-topmost", True)
        link_window.grab_set()
        link_window.configure(fg_color="white")
        
        ctk.CTkLabel(link_window, text="🔗 LIÊN KẾT DỊCH VỤ - VẬT TƯ", 
                    font=("Arial", 22, "bold"), text_color="#1e293b").pack(pady=20)
        
        # Main content frame
        main_frame = ctk.CTkFrame(link_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        main_frame.grid_columnconfigure((0, 1), weight=1)
        
        # ===== LEFT PANEL: DỊCH VỤ =====
        left_panel = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=5)
        left_panel.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(left_panel, text="📋 DỊCH VỤ", font=("Arial", 16, "bold"), text_color="#2563eb").pack(pady=10)
        
        # Search service
        service_search = ctk.CTkEntry(left_panel, placeholder_text="🔍 Tìm dịch vụ...", height=35)
        service_search.pack(fill="x", padx=10, pady=(0, 10))
        
        # Service list scrollable
        service_list_frame = ctk.CTkScrollableFrame(left_panel, fg_color="transparent", height=300)
        service_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Selected service display
        selected_service_frame = ctk.CTkFrame(left_panel, fg_color="#f1f5f9", corner_radius=8)
        selected_service_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(selected_service_frame, text="Đã chọn:", font=("Arial", 11, "bold"), text_color="#64748b").pack(anchor="w", padx=10, pady=(5, 0))
        self.selected_service_label = ctk.CTkLabel(selected_service_frame, text="Chưa có", font=("Arial", 13), text_color="#1e293b")
        self.selected_service_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # ===== RIGHT PANEL: VẬT TƯ =====
        right_panel = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=5)
        right_panel.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(right_panel, text="📦 VẬT TƯ", font=("Arial", 16, "bold"), text_color="#10b981").pack(pady=10)
        
        # Search product
        product_search = ctk.CTkEntry(right_panel, placeholder_text="🔍 Tìm vật tư...", height=35)
        product_search.pack(fill="x", padx=10, pady=(0, 10))
        
        # Product list scrollable
        product_list_frame = ctk.CTkScrollableFrame(right_panel, fg_color="transparent", height=300)
        product_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Selected product display
        selected_product_frame = ctk.CTkFrame(right_panel, fg_color="#f1f5f9", corner_radius=8)
        selected_product_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(selected_product_frame, text="Đã chọn:", font=("Arial", 11, "bold"), text_color="#64748b").pack(anchor="w", padx=10, pady=(5, 0))
        self.selected_product_label = ctk.CTkLabel(selected_product_frame, text="Chưa có", font=("Arial", 13), text_color="#1e293b")
        self.selected_product_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # ===== BOTTOM PANEL: DANH SÁCH LIÊN KẾT ĐÃ CHỌN =====
        bottom_panel = ctk.CTkFrame(link_window, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        bottom_panel.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(bottom_panel, text="📌 DANH SÁCH LIÊN KẾT SẼ THÊM", font=("Arial", 14, "bold"), text_color="#f59e0b").pack(anchor="w", padx=15, pady=10)
        
        # List of pending links
        self.pending_links = []  # List of dicts: {service_id, service_name, product_id, product_name, quantity}
        
        self.pending_frame = ctk.CTkScrollableFrame(bottom_panel, fg_color="#fef3c7", corner_radius=8, height=120)
        self.pending_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Quantity input
        qty_frame = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        qty_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(qty_frame, text="Số lượng cần:", font=("Arial", 13, "bold")).pack(side="left", padx=5)
        self.qty_entry = ctk.CTkEntry(qty_frame, width=80, justify="center")
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(qty_frame, text="(Có thể sửa sau)", font=("Arial", 11), text_color="#64748b").pack(side="left", padx=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=15)
        
        self.add_btn = ctk.CTkButton(btn_frame, text="➕ Thêm vào danh sách", fg_color="#f59e0b", hover_color="#d97706",
                                    height=40, command=self.add_to_pending, state="disabled")
        self.add_btn.pack(side="left", fill="x", expand=True, padx=5)
        
        self.save_btn = ctk.CTkButton(btn_frame, text="💾 Lưu tất cả liên kết", fg_color="#10b981", hover_color="#059669",
                                     height=40, command=self.save_all_links, state="disabled")
        self.save_btn.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(btn_frame, text="Đóng", fg_color="transparent", text_color="#64748b",
                     height=40, command=link_window.destroy).pack(side="left", fill="x", expand=True, padx=5)
        
        # Store variables
        self.link_window = link_window
        self.selected_service_id = None
        self.selected_service_name = None
        self.selected_product_id = None
        self.selected_product_name = None
        self.current_stock = 0
        
        # Load data
        self.load_services_with_search(service_list_frame, service_search)
        self.load_products_with_search(product_list_frame, product_search)
    
    def load_services_with_search(self, container, search_entry):
        """Tải danh sách dịch vụ có tìm kiếm"""
        def load():
            for w in container.winfo_children():
                w.destroy()
            
            db = connect_db()
            if db:
                cursor = db.cursor()
                search = f"%{search_entry.get()}%"
                cursor.execute("SELECT id, service_name, require_inventory FROM services WHERE status = 1 AND service_name LIKE %s", (search,))
                services = cursor.fetchall()
                
                for s in services:
                    btn = ctk.CTkButton(
                        container, text=s[1], 
                        fg_color="#f1f5f9" if s[2] else "#e2e8f0",
                        text_color="#1e293b", height=35,
                        corner_radius=6,
                        command=lambda sid=s[0], name=s[1]: self.select_service(sid, name)
                    )
                    btn.pack(fill="x", pady=2)
                cursor.close()
                db.close()
        
        search_entry.bind("<KeyRelease>", lambda e: load())
        load()
    
    def load_products_with_search(self, container, search_entry):
        """Tải danh sách vật tư có tìm kiếm"""
        def load():
            for w in container.winfo_children():
                w.destroy()
            
            db = connect_db()
            if db:
                cursor = db.cursor()
                search = f"%{search_entry.get()}%"
                cursor.execute("SELECT id, product_name, stock_quantity, unit FROM inventory WHERE product_name LIKE %s", (search,))
                products = cursor.fetchall()
                
                for p in products:
                    btn = ctk.CTkButton(
                        container, text=f"{p[1]} (Tồn: {p[2]} {p[3]})",
                        fg_color="transparent", text_color="#1e293b", height=35,
                        corner_radius=6, anchor="w",
                        command=lambda pid=p[0], name=p[1], stock=p[2], unit=p[3]: self.select_product(pid, name, stock, unit)
                    )
                    btn.pack(fill="x", pady=2)
                cursor.close()
                db.close()
        
        search_entry.bind("<KeyRelease>", lambda e: load())
        load()
    
    def select_service(self, sid, name):
        self.selected_service_id = sid
        self.selected_service_name = name
        self.selected_service_label.configure(text=name, text_color="#2563eb")
        self.update_add_button_state()
    
    def select_product(self, pid, name, stock, unit):
        self.selected_product_id = pid
        self.selected_product_name = name
        self.current_stock = stock
        self.current_unit = unit
        self.selected_product_label.configure(text=f"{name} (Tồn: {stock} {unit})", text_color="#10b981")
        self.update_add_button_state()
    
    def update_add_button_state(self):
        if self.selected_service_id and self.selected_product_id:
            self.add_btn.configure(state="normal")
        else:
            self.add_btn.configure(state="disabled")
    
    def add_to_pending(self):
        try:
            quantity = int(self.qty_entry.get())
            if quantity <= 0:
                quantity = 1
        except:
            quantity = 1
        
        # Kiểm tra tồn kho
        if quantity > self.current_stock:
            if not messagebox.askyesno("Cảnh báo", f"Số lượng {quantity} vượt quá tồn kho ({self.current_stock}). Vẫn tiếp tục?"):
                return
        
        # Kiểm tra trùng lặp
        for link in self.pending_links:
            if link["service_id"] == self.selected_service_id and link["product_id"] == self.selected_product_id:
                messagebox.showwarning("Trùng lặp", f"Liên kết {self.selected_service_name} - {self.selected_product_name} đã có trong danh sách!")
                return
        
        # Thêm vào danh sách
        self.pending_links.append({
            "service_id": self.selected_service_id,
            "service_name": self.selected_service_name,
            "product_id": self.selected_product_id,
            "product_name": self.selected_product_name,
            "quantity": quantity,
            "stock": self.current_stock,
            "unit": self.current_unit
        })
        
        # Cập nhật giao diện danh sách
        self.refresh_pending_list()
        
        # Kích hoạt nút lưu
        self.save_btn.configure(state="normal")
        
        # Reset selection
        self.selected_service_id = None
        self.selected_service_name = None
        self.selected_product_id = None
        self.selected_product_name = None
        self.selected_service_label.configure(text="Chưa có")
        self.selected_product_label.configure(text="Chưa có")
        self.add_btn.configure(state="disabled")
        self.qty_entry.delete(0, "end")
        self.qty_entry.insert(0, "1")
    
    def refresh_pending_list(self):
        """Làm mới danh sách liên kết đã chọn"""
        for w in self.pending_frame.winfo_children():
            w.destroy()
        
        if not self.pending_links:
            empty_label = ctk.CTkLabel(self.pending_frame, text="Chưa có liên kết nào được thêm", 
                                      font=("Arial", 12), text_color="#64748b")
            empty_label.pack(pady=20)
            return
        
        for idx, link in enumerate(self.pending_links):
            row_frame = ctk.CTkFrame(self.pending_frame, fg_color="white", corner_radius=6, border_width=1, border_color="#fde68a")
            row_frame.pack(fill="x", pady=3, padx=5)
            
            # Thông tin
            info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
            
            ctk.CTkLabel(info_frame, text=f"📋 {link['service_name']}", font=("Arial", 13, "bold"), text_color="#2563eb").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"🔧 {link['product_name']}", font=("Arial", 12), text_color="#1e293b").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Số lượng: {link['quantity']} {link['unit']} (Tồn: {link['stock']} {link['unit']})", 
                        font=("Arial", 11), text_color="#64748b").pack(anchor="w")
            
            # Nút chỉnh sửa và xóa
            btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=8)
            
            # Nút chỉnh sửa số lượng
            def edit_quantity(idx=idx):
                new_qty = ctk.CTkInputDialog(text=f"Nhập số lượng mới cho {link['product_name']}:", 
                                            title="Sửa số lượng").get_input()
                if new_qty and new_qty.isdigit():
                    new_qty_int = int(new_qty)
                    if new_qty_int > 0:
                        self.pending_links[idx]["quantity"] = new_qty_int
                        self.refresh_pending_list()
            
            ctk.CTkButton(btn_frame, text="✏️", width=35, height=32, corner_radius=6,
                         fg_color="#f1f5f9", text_color="#64748b",
                         command=edit_quantity).pack(side="left", padx=2)
            
            # Nút xóa
            def remove_link(idx=idx):
                if messagebox.askyesno("Xác nhận", f"Xóa liên kết {link['service_name']} - {link['product_name']}?"):
                    del self.pending_links[idx]
                    self.refresh_pending_list()
                    if not self.pending_links:
                        self.save_btn.configure(state="disabled")
            
            ctk.CTkButton(btn_frame, text="❌", width=35, height=32, corner_radius=6,
                         fg_color="#fff1f2", text_color="#ef4444",
                         command=remove_link).pack(side="left", padx=2)
    
    def save_all_links(self):
        """Lưu tất cả liên kết vào database"""
        if not self.pending_links:
            messagebox.showwarning("Thông báo", "Không có liên kết nào để lưu!")
            return
        
        db = connect_db()
        if not db:
            messagebox.showerror("Lỗi", "Không thể kết nối database!")
            return
        
        cursor = db.cursor()
        success_count = 0
        error_count = 0
        
        try:
            for link in self.pending_links:
                try:
                    # Cập nhật require_inventory cho dịch vụ
                    cursor.execute("UPDATE services SET require_inventory = TRUE WHERE id = %s", (link["service_id"],))
                    
                    # Thêm hoặc cập nhật liên kết
                    cursor.execute("""
                        INSERT INTO service_products (service_id, product_id, quantity_needed)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE quantity_needed = %s
                    """, (link["service_id"], link["product_id"], link["quantity"], link["quantity"]))
                    
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Lỗi khi lưu {link}: {e}")
            
            db.commit()
            
            # Thông báo kết quả
            if success_count > 0:
                messagebox.showinfo("Thành công", f"Đã lưu {success_count} liên kết thành công!\n{error_count} lỗi" if error_count > 0 else f"Đã lưu {success_count} liên kết thành công!")
            
            # Đóng cửa sổ và refresh
            self.link_window.destroy()
            self.load_inventory()
            
        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", f"Lỗi khi lưu: {e}")
        finally:
            db.close()

    def open_add_modal(self):
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
        ent_min.insert(0, "5")
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
            except Exception as e: 
                messagebox.showerror("Lỗi", f"Lỗi: {e}")
            finally: 
                db.close()

    def open_edit_modal(self, row):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Sửa: {row[2]}")
        modal.geometry("850x680")
        modal.after(10, modal.lift)
        modal.grab_set()

        ctk.CTkLabel(modal, text="Chỉnh sửa thông tin", font=("Arial", 22, "bold")).pack(pady=20)
        form_f = ctk.CTkFrame(modal, fg_color="transparent")
        form_f.pack(fill="both", expand=True, padx=45)
        form_f.grid_columnconfigure((0, 1), weight=1)

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
        
        ctk.CTkLabel(form_f, text="Vị trí").grid(row=8, column=0, columnspan=2, sticky="w")
        ent_loc = ctk.CTkEntry(form_f, height=40); ent_loc.insert(0, row[9] if row[9] else "")
        ent_loc.grid(row=9, column=0, columnspan=2, sticky="ew", pady=10)

        btn_save = ctk.CTkButton(modal, text="Lưu thay đổi", fg_color="#2563eb", height=45, width=150,
                                 command=lambda: self.update_item(row[0], ent_code.get(), ent_name.get(), cb_cat.get(),
                                                                ent_brand.get(), ent_stock.get(), cb_unit.get(), 
                                                                ent_price.get(), ent_loc.get(), modal))
        btn_save.pack(pady=20)

    def update_item(self, item_id, code, name, cat, brand, stock, unit, price, loc, window):
        db = connect_db()
        if db:
            cursor = db.cursor()
            try:
                sql = """UPDATE inventory SET product_code=%s, product_name=%s, category=%s, brand=%s, 
                         stock_quantity=%s, unit=%s, price=%s, location=%s WHERE id=%s"""
                cursor.execute(sql, (code, name, cat, brand, int(stock), unit, float(price), loc, item_id))
                db.commit()
                messagebox.showinfo("Thành công", "Đã cập nhật!")
                window.destroy()
                self.load_inventory()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))
            finally: 
                db.close()

    def delete_item(self, item_id, item_name):
        if messagebox.askyesno("Xác nhận", f"Xóa '{item_name}'?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
                db.commit()
                db.close()
                self.load_inventory()


if __name__ == "__main__":
    pass