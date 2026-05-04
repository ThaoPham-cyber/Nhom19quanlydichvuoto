import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from database import connect_db
import os
from PIL import Image


class GroupedProductSelectionWindow(ctk.CTkToplevel):
    """Cửa sổ chọn và nhập số lượng vật tư gộp từ nhiều hóa đơn"""
    def __init__(self, parent, grouped_products, callback, total_service_amount, paid_amount, total_amount_label, payment_amount_label):
        super().__init__(parent)
        self.parent = parent
        self.grouped_products = grouped_products
        self.callback = callback
        self.total_service_amount = total_service_amount
        self.paid_amount = paid_amount
        self.total_amount_label = total_amount_label
        self.payment_amount_label = payment_amount_label
        self.selected_products = []

        self.title("Chọn vật tư đã sử dụng (gộp)")
        self.geometry("700x550")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="white")

        ctk.CTkLabel(self, text="NHẬP VẬT TƯ ĐÃ SỬ DỤNG (GỘP)", font=("Arial", 20, "bold"),
                    text_color="#1e293b").pack(pady=20)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)
        ctk.CTkLabel(main_frame, text="📦 VẬT TƯ CẦN CHO DỊCH VỤ", font=("Arial", 14, "bold"),
                    text_color="#2563eb").pack(anchor="w", pady=(0, 10))

        self.products_frame = ctk.CTkScrollableFrame(main_frame, fg_color="#f8fafc", corner_radius=10)
        self.products_frame.pack(fill="both", expand=True)

        self.entries = {}
        for prod in grouped_products:
            card = ctk.CTkFrame(self.products_frame, fg_color="white", corner_radius=10,
                               border_width=1, border_color="#e2e8f0")
            card.pack(fill="x", pady=5, padx=5)

            name_frame = ctk.CTkFrame(card, fg_color="transparent")
            name_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            ctk.CTkLabel(name_frame, text=prod['name'], font=("Arial", 14, "bold"),
                        text_color="#1e293b").pack(anchor="w")
            info_text = f"Cần: {prod['total_needed']} {prod['unit']} | Tồn kho: {prod['stock']} {prod['unit']}"
            stock_color = "#ef4444" if prod['stock'] < prod['total_needed'] else "#64748b"
            ctk.CTkLabel(name_frame, text=info_text, font=("Arial", 11), text_color=stock_color).pack(anchor="w")
            ctk.CTkLabel(name_frame, text=f"Giá: {int(prod['price']):,} ₫/{prod['unit']}", font=("Arial", 11),
                        text_color="#10b981").pack(anchor="w")

            right_frame = ctk.CTkFrame(card, fg_color="transparent")
            right_frame.pack(side="right", padx=15, pady=10)
            ctk.CTkLabel(right_frame, text="Số lượng sử dụng:", font=("Arial", 12)).pack(side="left", padx=5)
            entry = ctk.CTkEntry(right_frame, width=80, justify="center")
            entry.insert(0, str(prod['total_needed']))
            entry.pack(side="left", padx=5)

            def validate(e, pid=prod['id'], max_q=prod['stock'], need=prod['total_needed']):
                try:
                    val = int(e.get())
                    if val < 0:
                        e.delete(0, "end")
                        e.insert(0, "0")
                    elif val > max_q:
                        e.delete(0, "end")
                        e.insert(0, str(max_q))
                        messagebox.showwarning("Cảnh báo", f"Tồn kho không đủ! Chỉ còn {max_q} {prod['unit']}")
                except:
                    e.delete(0, "end")
                    e.insert(0, str(need))
            entry.bind("<KeyRelease>", validate)

            self.entries[prod['id']] = {
                'entry': entry,
                'data': prod
            }

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Hủy", fg_color="transparent", text_color="#64748b",
                     height=40, command=self.destroy).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="✅ Xác nhận sử dụng", fg_color="#10b981", hover_color="#059669",
                     height=40, command=self.confirm).pack(side="right", fill="x", expand=True, padx=5)

    def confirm(self):
        self.selected_products = []
        total_product_cost = 0
        for pid, ent in self.entries.items():
            try:
                qty = int(ent['entry'].get())
                if qty > 0:
                    prod = ent['data']
                    self.selected_products.append({
                        'id': pid,
                        'name': prod['name'],
                        'quantity': qty,
                        'price': prod['price'],
                        'unit': prod['unit'],
                        'invoices_needs': prod.get('invoices_needs', {})
                    })
                    total_product_cost += qty * prod['price']
            except:
                pass
        self.destroy()
        if self.callback:
            self.callback(self.selected_products, total_product_cost)


class ProductSelectionWindow(ctk.CTkToplevel):
    """Cửa sổ chọn và nhập số lượng vật tư đã sử dụng (cho 1 hóa đơn)"""
    def __init__(self, parent, service_id, service_name, invoice_id, callback, initial_products=None):
        super().__init__(parent)
        self.parent = parent
        self.service_id = service_id
        self.service_name = service_name
        self.invoice_id = invoice_id
        self.callback = callback
        self.selected_products = []
        self.initial_products = {prod['id']: prod for prod in (initial_products or [])}

        self.title(f"Chọn vật tư đã sử dụng - {service_name}")
        self.geometry("700x550")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="white")

        ctk.CTkLabel(self, text=f"NHẬP VẬT TƯ ĐÃ SỬ DỤNG", font=("Arial", 20, "bold"),
                    text_color="#1e293b").pack(pady=20)
        ctk.CTkLabel(self, text=f"Dịch vụ: {service_name}", font=("Arial", 14),
                    text_color="#64748b").pack()

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)
        ctk.CTkLabel(main_frame, text="📦 VẬT TƯ CẦN CHO DỊCH VỤ", font=("Arial", 14, "bold"),
                    text_color="#2563eb").pack(anchor="w", pady=(0, 10))

        self.products_frame = ctk.CTkScrollableFrame(main_frame, fg_color="#f8fafc", corner_radius=10)
        self.products_frame.pack(fill="both", expand=True)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Hủy", fg_color="transparent", text_color="#64748b",
                     height=40, command=self.destroy).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="✅ Xác nhận sử dụng", fg_color="#10b981", hover_color="#059669",
                     height=40, command=self.confirm_products).pack(side="right", fill="x", expand=True, padx=5)

        self.load_required_products()

    def load_required_products(self):
        for w in self.products_frame.winfo_children():
            w.destroy()
        db = connect_db()
        if not db:
            ctk.CTkLabel(self.products_frame, text="Lỗi kết nối database!",
                        font=("Arial", 12), text_color="#ef4444").pack(pady=20)
            return

        cursor = db.cursor()
        cursor.execute("""
            SELECT p.id, p.product_name, sp.quantity_needed, p.stock_quantity, p.price, p.unit
            FROM service_products sp
            JOIN inventory p ON sp.product_id = p.id
            WHERE sp.service_id = %s
        """, (self.service_id,))
        products = cursor.fetchall()
        cursor.close()
        db.close()

        if not products:
            ctk.CTkLabel(self.products_frame, text="Dịch vụ này không yêu cầu vật tư nào.\nBạn có thể tiếp tục thanh toán.",
                        font=("Arial", 12), text_color="#64748b").pack(pady=20)
            return

        self.product_entries = {}
        for prod in products:
            prod_id, prod_name, needed, stock, price, unit = prod
            needed = int(needed) if needed is not None else 0
            stock = int(stock) if stock is not None else 0
            price = float(price) if price is not None else 0.0

            card = ctk.CTkFrame(self.products_frame, fg_color="white", corner_radius=10,
                               border_width=1, border_color="#e2e8f0")
            card.pack(fill="x", pady=5, padx=5)

            name_frame = ctk.CTkFrame(card, fg_color="transparent")
            name_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            ctk.CTkLabel(name_frame, text=prod_name, font=("Arial", 14, "bold"),
                        text_color="#1e293b").pack(anchor="w")
            info_text = f"Cần: {needed} {unit} | Tồn kho: {stock} {unit}"
            stock_color = "#ef4444" if stock < needed else "#64748b"
            ctk.CTkLabel(name_frame, text=info_text, font=("Arial", 11), text_color=stock_color).pack(anchor="w")
            ctk.CTkLabel(name_frame, text=f"Giá: {int(price):,} ₫/{unit}", font=("Arial", 11),
                        text_color="#10b981").pack(anchor="w")

            right_frame = ctk.CTkFrame(card, fg_color="transparent")
            right_frame.pack(side="right", padx=15, pady=10)
            ctk.CTkLabel(right_frame, text="Số lượng sử dụng:", font=("Arial", 12)).pack(side="left", padx=5)
            entry = ctk.CTkEntry(right_frame, width=80, justify="center")
            current_quantity = self.initial_products.get(prod_id, {}).get('quantity', needed)
            entry.insert(0, str(current_quantity))
            entry.pack(side="left", padx=5)

            def validate_quantity(e, pid=prod_id, max_q=stock, need=needed, u=unit):
                try:
                    val = int(e.get())
                    if val > max_q:
                        e.delete(0, "end")
                        e.insert(0, str(max_q))
                        messagebox.showwarning("Cảnh báo", f"Tồn kho không đủ! Chỉ còn {max_q} {u}")
                    elif val < 0:
                        e.delete(0, "end")
                        e.insert(0, "0")
                except:
                    e.delete(0, "end")
                    e.insert(0, str(need))
            entry.bind("<KeyRelease>", lambda e, ent=entry, pid=prod_id: validate_quantity(e, pid=pid))

            self.product_entries[prod_id] = {
                "entry": entry,
                "name": prod_name,
                "price": price,
                "unit": unit,
                "stock": stock,
                "needed": needed
            }

    def confirm_products(self):
        self.selected_products = []
        for prod_id, data in self.product_entries.items():
            try:
                quantity = int(data["entry"].get())
                if quantity > 0:
                    self.selected_products.append({
                        "id": prod_id,
                        "name": data["name"],
                        "quantity": quantity,
                        "price": data["price"],
                        "unit": data["unit"]
                    })
            except:
                pass
        self.destroy()
        if self.callback:
            self.callback(self.selected_products)


class PaymentFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.parent_app = parent
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Thanh toán", font=("Arial", 28, "bold"),
                     text_color="#1e293b").pack(side="left")
        control_frame = ctk.CTkFrame(header, fg_color="transparent")
        control_frame.pack(side="right")
        self.refresh_btn = ctk.CTkButton(control_frame, text="🔄 Làm mới", width=100, height=35,
                                         fg_color="#3b82f6", command=self.refresh_all_data)
        self.refresh_btn.pack(side="left", padx=5)
        self.last_update_label = ctk.CTkLabel(control_frame, text="", font=("Arial", 10),
                                             text_color="#64748b")
        self.last_update_label.pack(side="left", padx=10)
        sync_btn = ctk.CTkButton(control_frame, text="🔄 Đồng bộ hóa", width=120, height=35,
                                 fg_color="#10b981", command=self.sync_invoices_from_appointments)
        sync_btn.pack(side="left", padx=5)
        history_btn = ctk.CTkButton(control_frame, text="📜 Lịch sử", width=100, height=35,
                                   fg_color="#8b5cf6", hover_color="#7c3aed",
                                   command=self.show_payment_history)
        history_btn.pack(side="left", padx=5)

        # Statistics
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 20))
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        self.total_revenue_card = self.create_stat_card(stats_frame, 0, "Tổng doanh thu", "0 ₫", "#3b82f6")
        self.total_paid_card = self.create_stat_card(stats_frame, 1, "Đã thu (hôm nay)", "0 ₫", "#10b981")
        self.total_remaining_card = self.create_stat_card(stats_frame, 2, "Còn lại (chưa thu)", "0 ₫", "#ef4444")
        self.total_partial_card = self.create_stat_card(stats_frame, 3, "Thanh toán 1 phần", "0", "#f59e0b")

        # Search
        search_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12,
                                    border_width=1, border_color="#e2e8f0")
        search_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 15))
        self.search_entry = ctk.CTkEntry(search_frame,
                                        placeholder_text="🔍 Tìm kiếm theo mã hóa đơn, khách hàng, biển số...",
                                        border_width=0, fg_color="transparent", height=45)
        self.search_entry.pack(fill="x", padx=15)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_invoices())

        # Table
        self.main_table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.main_table_frame.grid(row=3, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.main_table_frame.grid_columnconfigure(0, weight=1)
        self.main_table_frame.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self.main_table_frame, fg_color="transparent", height=50)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))
        headers = ["Mã HĐ", "Khách hàng", "Biển số", "Dịch vụ", "Ngày", "Tổng tiền",
                   "Đã thanh toán", "Còn lại", "Vật tư", "Trạng thái", "Thao tác"]
        for i, text in enumerate(headers):
            ctk.CTkLabel(header_frame, text=text, font=("Arial", 12, "bold"),
                        text_color="#64748b").grid(row=0, column=i, padx=10, pady=10, sticky="w")
        for i in range(len(headers)):
            header_frame.grid_columnconfigure(i, weight=1)

        self.scroll_data = ctk.CTkScrollableFrame(self.main_table_frame, fg_color="transparent",
                                                   corner_radius=0)
        self.scroll_data.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        for i in range(len(headers)):
            self.scroll_data.grid_columnconfigure(i, weight=1, uniform='tablecol')

        self.load_invoices()

    def refresh_all_data(self):
        self.load_invoices()
        self.last_update_label.configure(text=f"📍 {datetime.now().strftime('%H:%M:%S')}")

    def create_stat_card(self, parent, col, title, value, color):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12, height=100)
        card.grid(row=0, column=col, sticky="nsew", padx=5)
        ctk.CTkLabel(card, text=title, font=("Arial", 13), text_color="#64748b").pack(anchor="w", padx=15, pady=(15, 5))
        stat_label = ctk.CTkLabel(card, text=value, font=("Arial", 24, "bold"), text_color=color)
        stat_label.pack(anchor="w", padx=15, pady=(0, 15))
        return stat_label

    def sync_invoices_from_appointments(self):
        db = connect_db()
        if not db:
            messagebox.showerror("Lỗi", "Không thể kết nối database!")
            return
        cursor = db.cursor()
        created_count = 0
        try:
            cursor.execute("""
                SELECT a.id, a.customer_id, a.car_plate, a.appointment_date,
                       s.id as service_id, s.service_name, s.price
                FROM appointments a
                LEFT JOIN services s ON a.service_id = s.id
                LEFT JOIN invoices i ON a.id = i.appointment_id
                WHERE i.id IS NULL 
                AND a.status IN ('Đã xác nhận', 'Đã hoàn thành', 'Đã bàn giao')
            """)
            appointments = cursor.fetchall()
            for appt in appointments:
                total = float(appt[6]) if appt[6] is not None else 0.0
                cursor.execute("""
                    INSERT INTO invoices (appointment_id, customer_id, total_amount, status, created_at)
                    VALUES (%s, %s, %s, 'Chưa thanh toán', NOW())
                """, (appt[0], appt[1], total))
                invoice_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO invoice_items (invoice_id, service_id, service_name, price, quantity)
                    VALUES (%s, %s, %s, %s, 1)
                """, (invoice_id, appt[4], appt[5], total))
                created_count += 1
            db.commit()
            if created_count > 0:
                messagebox.showinfo("Thành công", f"Đã tạo {created_count} hóa đơn mới!")
            else:
                messagebox.showinfo("Thông báo", "Không có hóa đơn mới để đồng bộ!")
            self.load_invoices()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", f"Lỗi đồng bộ: {e}")
        finally:
            db.close()

    def load_invoices(self):
        for w in self.scroll_data.winfo_children():
            w.destroy()
        db = connect_db()
        if not db:
            return
        cursor = db.cursor()
        search = f"%{self.search_entry.get()}%"
        query = """
            SELECT
                c.id AS customer_id,
                c.full_name,
                GROUP_CONCAT(DISTINCT COALESCE(a.car_plate, 'Chưa cập nhật') SEPARATOR ', ') AS car_plate,
                SUM(i.total_amount) AS total_amount,
                COALESCE(SUM(p.paid_amount), 0) AS paid_amount,
                MIN(i.created_at) AS created_at,
                GROUP_CONCAT(DISTINCT i.id ORDER BY i.id SEPARATOR ',') AS invoice_ids,
                GROUP_CONCAT(DISTINCT ii.service_name SEPARATOR ', ') AS services
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            LEFT JOIN appointments a ON i.appointment_id = a.id
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) AS paid_amount
                FROM payments
                GROUP BY invoice_id
            ) p ON p.invoice_id = i.id
            LEFT JOIN invoice_items ii ON ii.invoice_id = i.id
            WHERE (c.full_name LIKE %s OR c.phone LIKE %s OR CAST(i.id AS CHAR) LIKE %s)
            AND i.status != 'Đã thanh toán'
            GROUP BY c.id, c.full_name
            ORDER BY MIN(i.created_at) DESC
        """
        cursor.execute(query, (search, search, search))
        invoices = cursor.fetchall()

        # Thống kê
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices")
        total_revenue_all = float(cursor.fetchone()[0] or 0)
        today = datetime.now().date()
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE DATE(payment_date) = %s", (today,))
        today_paid = float(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE status != 'Đã thanh toán'")
        remaining_unpaid = float(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE status = 'Thanh toán một phần'")
        partial_count = cursor.fetchone()[0] or 0

        self.total_revenue_card.configure(text=f"{int(total_revenue_all):,} ₫")
        self.total_paid_card.configure(text=f"{int(today_paid):,} ₫")
        self.total_remaining_card.configure(text=f"{int(remaining_unpaid):,} ₫")
        self.total_partial_card.configure(text=f"{partial_count}")

        if not invoices:
            empty_label = ctk.CTkLabel(self.scroll_data,
                text="📭 Không có hóa đơn nào cần thanh toán\n\nNhấn 'Đồng bộ hóa' để tạo hóa đơn từ lịch hẹn",
                font=("Arial", 14), text_color="#64748b")
            empty_label.pack(pady=50)
            db.close()
            return

        for idx, inv in enumerate(invoices):
            customer_id = inv[0]
            customer = inv[1]
            car_plate = inv[2] if inv[2] else "Chưa cập nhật"
            total = float(inv[3] or 0)
            paid = float(inv[4] or 0)
            created_at = inv[5]
            invoice_ids = inv[6] or ""
            services = inv[7] if inv[7] else "Chưa có"
            remaining = total - paid

            if len(services) > 40:
                services = services[:37] + "..."

            invoice_id_list = [int(x) for x in invoice_ids.split(",") if x.strip()]
            invoice_display = f"HD{invoice_id_list[0]:04d}" if invoice_id_list else "---"
            if len(invoice_id_list) > 1:
                invoice_display += f" +{len(invoice_id_list) - 1}"

            plates = [p.strip() for p in car_plate.split(",") if p.strip()]
            if plates:
                car_plate = plates[0]
                if len(plates) > 1:
                    car_plate += f" +{len(plates) - 1}"
            else:
                car_plate = "Chưa cập nhật"

            service_names = [s.strip() for s in services.split(",") if s.strip()]
            if service_names:
                services = service_names[0]
                if len(service_names) > 1:
                    services += f" +{len(service_names) - 1}"
            else:
                services = "Chưa có"

            if invoice_id_list:
                placeholders = ','.join(['%s'] * len(invoice_id_list))
                cursor.execute(f"SELECT COUNT(*) FROM invoice_products WHERE invoice_id IN ({placeholders})", tuple(invoice_id_list))
                has_products = cursor.fetchone()[0] > 0
            else:
                has_products = False
            product_status = "✅ Đã chọn" if has_products else "⚠️ Chưa chọn"
            product_color = "#10b981" if has_products else "#f59e0b"

            if remaining <= 0:
                status_color = "#10b981"
                status_text = "Đã thanh toán"
                actual_status = "Đã thanh toán"
            elif paid > 0 and remaining > 0:
                status_color = "#f59e0b"
                status_text = "Thanh toán 1 phần"
                actual_status = "Thanh toán một phần"
            else:
                status_color = "#ef4444"
                status_text = "Chưa thanh toán"
                actual_status = "Chưa thanh toán"

            row_idx = idx * 2
            display_customer = customer if len(customer) <= 20 else customer[:17] + "..."
            display_plate = car_plate if len(car_plate) <= 15 else car_plate[:12] + "..."
            display_services = services if len(services) <= 20 else services[:17] + "..."
            ctk.CTkLabel(self.scroll_data, text=invoice_display, font=("Arial", 13, "bold"), text_color="#2563eb").grid(row=row_idx, column=0, padx=0, pady=12, sticky="ew")
            ctk.CTkLabel(self.scroll_data, text=display_customer, font=("Arial", 13)).grid(row=row_idx, column=1, padx=2, pady=12, sticky="ew")
            ctk.CTkLabel(self.scroll_data, text=display_plate, font=("Arial", 12), text_color="#64748b").grid(row=row_idx, column=2, padx=2, pady=12, sticky="ew")
            ctk.CTkLabel(self.scroll_data, text=display_services, font=("Arial", 12)).grid(row=row_idx, column=3, padx=2, pady=12, sticky="ew")
            date_str = created_at.strftime("%d/%m/%Y") if created_at else ""
            ctk.CTkLabel(self.scroll_data, text=date_str, font=("Arial", 12)).grid(row=row_idx, column=4, padx=2, pady=12, sticky="ew")
            ctk.CTkLabel(self.scroll_data, text=f"{int(total):,} ₫", font=("Arial", 13, "bold"), text_color="#1e293b").grid(row=row_idx, column=5, padx=2, pady=12, sticky="ew")
            ctk.CTkLabel(self.scroll_data, text=f"{int(paid):,} ₫", font=("Arial", 13)).grid(row=row_idx, column=6, padx=2, pady=12, sticky="ew")
            ctk.CTkLabel(self.scroll_data, text=f"{int(remaining):,} ₫", font=("Arial", 13, "bold"), text_color="#ef4444" if remaining > 0 else "#10b981").grid(row=row_idx, column=7, padx=2, pady=12, sticky="ew")

            product_btn = ctk.CTkButton(self.scroll_data, text=product_status, width=70, height=28,
                                       fg_color=product_color, text_color="white", font=("Arial", 10),
                                       command=lambda ids=invoice_id_list: self.view_invoice_products(ids))
            product_btn.grid(row=row_idx, column=8, padx=0, pady=12)

            status_badge = ctk.CTkLabel(self.scroll_data, text=status_text, font=("Arial", 11, "bold"),
                                        fg_color=status_color, corner_radius=6, padx=8)
            status_badge.grid(row=row_idx, column=9, padx=2, pady=12)

            btn_frame = ctk.CTkFrame(self.scroll_data, fg_color="transparent")
            btn_frame.grid(row=row_idx, column=10, padx=2, pady=12, sticky="ew")
            customer_data = (customer_id, customer, car_plate, total, paid, created_at, invoice_ids, services, invoice_id_list)

            if actual_status == "Chưa thanh toán":
                ctk.CTkButton(btn_frame, text="🛒 Toàn phần", width=80, height=32,
                             fg_color="#10b981", hover_color="#059669",
                             command=lambda i=customer_data: self.full_payment(i)).grid(row=0, column=0, padx=1, pady=1, sticky="ew")
                ctk.CTkButton(btn_frame, text="💰 1 phần", width=80, height=32,
                             fg_color="#f59e0b", hover_color="#d97706",
                             command=lambda i=customer_data: self.partial_payment(i)).grid(row=0, column=1, padx=1, pady=1, sticky="ew")
                btn_frame.grid_columnconfigure(0, weight=1)
                btn_frame.grid_columnconfigure(1, weight=1)
            elif actual_status == "Thanh toán một phần" and remaining > 0:
                ctk.CTkButton(btn_frame, text="🛒 Thanh toán tiếp", width=100, height=32,
                             fg_color="#3b82f6", hover_color="#2563eb",
                             command=lambda i=customer_data, r=remaining: self.continue_payment(i, r)).grid(row=0, column=0, columnspan=2, padx=1, pady=1, sticky="ew")
            elif actual_status == "Đã thanh toán":
                ctk.CTkLabel(btn_frame, text="✅", font=("Arial", 18)).grid(row=0, column=0, columnspan=2, padx=1, pady=1, sticky="ew")

            ctk.CTkFrame(self.scroll_data, height=1, fg_color="#f1f5f9").grid(row=row_idx+1, column=0, columnspan=11, sticky="ew")
        db.close()

    def view_invoice_products(self, invoice_ids):
        view_window = ctk.CTkToplevel(self)
        view_window.title("Vật tư đã sử dụng")
        view_window.geometry("600x400")
        view_window.attributes("-topmost", True)
        view_window.grab_set()
        view_window.configure(fg_color="white")
        ctk.CTkLabel(view_window, text="📦 VẬT TƯ ĐÃ SỬ DỤNG", font=("Arial", 20, "bold"), text_color="#1e293b").pack(pady=20)
        main_frame = ctk.CTkScrollableFrame(view_window, fg_color="#f8fafc", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)
        db = connect_db()
        if db:
            cursor = db.cursor()
            if isinstance(invoice_ids, list):
                placeholders = ','.join(['%s'] * len(invoice_ids))
                cursor.execute(f"""
                    SELECT ip.product_name, ip.quantity, ip.price, p.unit
                    FROM invoice_products ip
                    LEFT JOIN inventory p ON ip.product_id = p.id
                    WHERE ip.invoice_id IN ({placeholders})
                """, tuple(invoice_ids))
            else:
                cursor.execute("""
                    SELECT ip.product_name, ip.quantity, ip.price, p.unit
                    FROM invoice_products ip
                    LEFT JOIN inventory p ON ip.product_id = p.id
                    WHERE ip.invoice_id = %s
                """, (invoice_ids,))
            products = cursor.fetchall()
            cursor.close()
            db.close()
            if products:
                total_cost = 0
                for p in products:
                    qty = int(p[1]) if p[1] is not None else 0
                    price = float(p[2]) if p[2] is not None else 0.0
                    unit = p[3] if p[3] else ""
                    card = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=8, border_width=1, border_color="#e2e8f0")
                    card.pack(fill="x", pady=5)
                    left = ctk.CTkFrame(card, fg_color="transparent")
                    left.pack(side="left", padx=15, pady=10)
                    ctk.CTkLabel(left, text=p[0], font=("Arial", 14, "bold")).pack(anchor="w")
                    ctk.CTkLabel(left, text=f"Số lượng: {qty} {unit}", font=("Arial", 11), text_color="#64748b").pack(anchor="w")
                    right = ctk.CTkFrame(card, fg_color="transparent")
                    right.pack(side="right", padx=15, pady=10)
                    total_price = qty * price
                    total_cost += total_price
                    ctk.CTkLabel(right, text=f"{int(price):,} ₫", font=("Arial", 14, "bold"), text_color="#10b981").pack(anchor="e")
                    ctk.CTkLabel(right, text=f"Thành tiền: {int(total_price):,} ₫", font=("Arial", 11), text_color="#64748b").pack(anchor="e")
                total_frame = ctk.CTkFrame(main_frame, fg_color="#f1f5f9", corner_radius=8)
                total_frame.pack(fill="x", pady=10)
                ctk.CTkLabel(total_frame, text=f"TỔNG GIÁ TRỊ VẬT TƯ: {int(total_cost):,} ₫", font=("Arial", 14, "bold"), text_color="#2563eb").pack(pady=10)
            else:
                ctk.CTkLabel(main_frame, text="Không có vật tư nào được sử dụng", font=("Arial", 14), text_color="#64748b").pack(pady=50)

    def full_payment(self, customer_row):
        total = float(customer_row[3])
        paid = float(customer_row[4])
        remaining = total - paid
        if remaining > 0:
            self.open_payment_modal(customer_row, remaining, is_partial=False)

    def partial_payment(self, customer_row):
        total = float(customer_row[3])
        paid = float(customer_row[4])
        remaining = total - paid
        if remaining <= 0:
            messagebox.showwarning("Thông báo", "Khách hàng này đã được thanh toán đủ!")
            return
        partial_amount = int(remaining * 0.4)
        if partial_amount <= 0:
            partial_amount = int(remaining)
        self.open_payment_modal(customer_row, partial_amount, is_partial=True)

    def continue_payment(self, customer_row, remaining):
        if remaining > 0:
            self.open_payment_modal(customer_row, remaining, is_partial=False)

    def find_qr_file(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "qr", "QR.png")
        if os.path.exists(path):
            print(f"✅ Tìm thấy QR tại: {path}")
            return path
        print(f"❌ Không tìm thấy QR tại: {path}")
        return None

    def get_grouped_products_for_invoices(self, invoice_ids):
        """Lấy danh sách vật tư cần cho nhiều hóa đơn, gộp các sản phẩm trùng nhau."""
        db = connect_db()
        if not db:
            return []
        cursor = db.cursor()
        # Lấy nhu cầu vật tư theo từng invoice dựa trên service_id
        invoice_needs = {}
        for inv_id in invoice_ids:
            cursor.execute("""
                SELECT ii.service_id
                FROM invoice_items ii
                WHERE ii.invoice_id = %s
            """, (inv_id,))
            svc_ids = [row[0] for row in cursor.fetchall()]
            needs = {}
            for svc_id in svc_ids:
                cursor.execute("SELECT require_inventory FROM services WHERE id = %s", (svc_id,))
                req = cursor.fetchone()
                if req and req[0] == 1:
                    cursor.execute("""
                        SELECT p.id, sp.quantity_needed
                        FROM service_products sp
                        JOIN inventory p ON sp.product_id = p.id
                        WHERE sp.service_id = %s
                    """, (svc_id,))
                    for pid, qty in cursor.fetchall():
                        qty = int(qty) if qty else 0
                        needs[pid] = needs.get(pid, 0) + qty
            invoice_needs[inv_id] = needs

        # Tập hợp tất cả product ids
        all_pids = set()
        for needs in invoice_needs.values():
            all_pids.update(needs.keys())
        if not all_pids:
            db.close()
            return []

        # Lấy thông tin chi tiết sản phẩm
        placeholders = ','.join(['%s'] * len(all_pids))
        cursor.execute(f"""
            SELECT id, product_name, unit, price, stock_quantity
            FROM inventory
            WHERE id IN ({placeholders})
        """, tuple(all_pids))
        products_info = {row[0]: {'name': row[1], 'unit': row[2], 'price': float(row[3]), 'stock': int(row[4])} for row in cursor.fetchall()}
        db.close()

        grouped = []
        for pid in all_pids:
            info = products_info[pid]
            total_needed = sum(invoice_needs[inv_id].get(pid, 0) for inv_id in invoice_ids)
            if total_needed == 0:
                continue
            grouped.append({
                'id': pid,
                'name': info['name'],
                'unit': info['unit'],
                'price': info['price'],
                'stock': info['stock'],
                'total_needed': total_needed,
                'invoices_needs': {inv_id: invoice_needs[inv_id].get(pid, 0) for inv_id in invoice_ids}
            })
        return grouped

    def open_product_selection(self, service_id, service_name, invoice_id, callback, initial_products=None):
        ProductSelectionWindow(self, service_id, service_name, invoice_id, callback, initial_products=initial_products)

    def show_qr_confirmation_dialog(self, invoice_display, payment_method, default_amount, payment_note, callback):
        """Dialog hiển thị QR code và thông tin thanh toán"""
        qr_dialog = ctk.CTkToplevel(self)
        qr_dialog.title(f"Xác nhận thanh toán - {payment_method}")
        qr_dialog.geometry("550x900")
        qr_dialog.attributes("-topmost", True)
        qr_dialog.grab_set()
        qr_dialog.configure(fg_color="white")
        qr_dialog.resizable(False, False)

        main_container = ctk.CTkFrame(qr_dialog, fg_color="white")
        main_container.pack(fill="both", expand=True, side="top")
        main_scroll = ctk.CTkScrollableFrame(main_container, fg_color="white")
        main_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        ctk.CTkLabel(main_scroll, text="📱 QUÉT MÃ QR ĐỂ THANH TOÁN", 
                    font=("Arial", 16, "bold"), text_color="#2563eb").pack(pady=(20, 10))

        qr_frame = ctk.CTkFrame(main_scroll, fg_color="#f8fafc", corner_radius=12, 
                                border_width=1, border_color="#e2e8f0")
        qr_frame.pack(fill="x", padx=20, pady=10)

        qr_path = self.find_qr_file()
        if qr_path:
            try:
                img = Image.open(qr_path)
                img = img.resize((280, 280), Image.Resampling.LANCZOS)
                qr_img = ctk.CTkImage(light_image=img, dark_image=img, size=(280, 280))
                qr_label = ctk.CTkLabel(qr_frame, image=qr_img, text="")
                qr_label.image = qr_img
                qr_label.pack(pady=15)
            except Exception as e:
                ctk.CTkLabel(qr_frame, text=f"❌ Lỗi tải ảnh QR\n{str(e)}", 
                            font=("Arial", 12), text_color="#ef4444").pack(pady=30)
        else:
            ctk.CTkLabel(qr_frame, text="📱 Chưa có file QR.png\nĐặt file QR.png vào thư mục 'qr/'", 
                        font=("Arial", 12), text_color="#f59e0b").pack(pady=30)

        info_frame = ctk.CTkFrame(main_scroll, fg_color="#f1f5f9", corner_radius=12)
        info_frame.pack(fill="x", padx=20, pady=10)
        if payment_method == "Chuyển khoản":
            bank_info = "🏦 VIETCOMBANK\n💳 Số TK: 123456789\n👤 Chủ TK: AUTOCARE"
        elif payment_method == "Momo":
            bank_info = "📱 VÍ MOMO\n📞 SĐT: 0987654321\n👤 Tên: AUTOCARE"
        else:
            bank_info = "📱 VÍ ZALOPAY\n📞 SĐT: 0123456789\n👤 Tên: AUTOCARE"
        ctk.CTkLabel(info_frame, text=bank_info, font=("Arial", 12), 
                    text_color="#1e293b", justify="left").pack(pady=15, padx=15)

        transaction_frame = ctk.CTkFrame(main_scroll, fg_color="white", corner_radius=12,
                                        border_width=1, border_color="#e2e8f0")
        transaction_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(transaction_frame, text="THÔNG TIN GIAO DỊCH", font=("Arial", 12, "bold"),
                    text_color="#1e293b").pack(anchor="w", padx=15, pady=(10, 5))
        trans_info = [
            ("Mã HĐ:", f"{invoice_display}"),
            ("Nội dung CK:", f"{invoice_display}"),
            ("Số tiền:", f"{int(default_amount):,} ₫")
        ]
        for label, value in trans_info:
            row = ctk.CTkFrame(transaction_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=label, font=("Arial", 11), text_color="#64748b").pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Arial", 11, "bold"), text_color="#ef4444").pack(side="right")
        ctk.CTkLabel(transaction_frame, text="(Nêu rõ mã hóa đơn trong nội dung chuyển khoản)", 
                    font=("Arial", 10), text_color="#94a3b8").pack(pady=(0, 10))

        ctk.CTkLabel(main_scroll, text="⚠️ Vui lòng kiểm tra kỹ thông tin trước khi gửi tiền",
                    font=("Arial", 11), text_color="#f97316").pack(pady=10)

        btn_frame = ctk.CTkFrame(qr_dialog, fg_color="white", border_width=1, border_color="#e2e8f0", height=60)
        btn_frame.pack(fill="x", padx=0, pady=0, side="bottom")
        btn_frame.pack_propagate(False)

        def confirm_action():
            callback()
            qr_dialog.destroy()

        cancel_btn = ctk.CTkButton(btn_frame, text="Quay lại", fg_color="transparent", text_color="#64748b",
                     hover_color="#f1f5f9", height=45, command=qr_dialog.destroy)
        cancel_btn.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        confirm_btn = ctk.CTkButton(btn_frame, text="✅ Đã chuyển khoản thành công", fg_color="#10b981", 
                     hover_color="#059669", height=45, command=confirm_action)
        confirm_btn.pack(side="right", fill="both", expand=True, padx=10, pady=8)

    def open_payment_modal(self, customer_row, default_amount, is_partial=False):
        modal = ctk.CTkToplevel(self)
        modal.title("Thanh toán hóa đơn")
        modal.geometry("700x1050")
        modal.attributes("-topmost", True)
        modal.grab_set()
        modal.configure(fg_color="white")
        modal.resizable(False, False)

        customer_id = customer_row[0]
        customer_name = customer_row[1]
        total_amount = float(customer_row[3])
        paid_amount = float(customer_row[4])
        created_at = customer_row[5]
        invoice_ids = customer_row[6] or ""
        invoice_id_list = [int(x) for x in invoice_ids.split(",") if x.strip()]
        default_amount = float(default_amount)

        invoice_display = f"HD{invoice_id_list[0]:04d}" if invoice_id_list else "---"
        if len(invoice_id_list) > 1:
            invoice_display += f" +{len(invoice_id_list) - 1}"

        if is_partial:
            percent = int((default_amount / total_amount) * 100) if total_amount > 0 else 0
            header_text = f"Thanh toán 1 phần ({percent}% - {int(default_amount):,}₫)"
        else:
            header_text = "Thanh toán hóa đơn"

        ctk.CTkLabel(modal, text=header_text, font=("Arial", 22, "bold"), text_color="#1e293b").pack(pady=(30, 20))
        form_frame = ctk.CTkFrame(modal, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=40)

        # Thông tin hóa đơn
        info_frame = ctk.CTkFrame(form_frame, fg_color="#f8fafc", corner_radius=12)
        info_frame.pack(fill="x", pady=(0, 20))
        info_fields = [
            ("Mã hóa đơn", invoice_display),
            ("Khách hàng", customer_name),
            ("Tổng tiền", f"{int(total_amount):,} ₫"),
            ("Đã thanh toán", f"{int(paid_amount):,} ₫"),
            ("Số tiền cần TT", f"{int(default_amount):,} ₫")
        ]
        total_label = None
        payment_label = None
        for label, value in info_fields:
            row_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(row_frame, text=label, font=("Arial", 13), text_color="#64748b").pack(side="left")
            value_color = "#ef4444" if "cần TT" in label else "#1e293b"
            lbl = ctk.CTkLabel(row_frame, text=value, font=("Arial", 14, "bold"), text_color=value_color)
            lbl.pack(side="right")
            if label == "Tổng tiền":
                total_label = lbl
            elif label == "Số tiền cần TT":
                payment_label = lbl

        selected_products = []
        product_summary_label = None

        # Xử lý vật tư gộp khi có nhiều hóa đơn
        if len(invoice_id_list) > 1:
            grouped_products = self.get_grouped_products_for_invoices(invoice_id_list)
            if grouped_products:
                product_frame = ctk.CTkFrame(form_frame, fg_color="#fff7ed", corner_radius=12,
                                            border_width=1, border_color="#f97316")
                product_frame.pack(fill="x", pady=10)
                ctk.CTkLabel(product_frame, text="📦 VẬT TƯ TIÊU HAO (GỘP)", font=("Arial", 13, "bold"),
                            text_color="#f97316").pack(anchor="w", padx=15, pady=(10, 5))
                product_summary_label = ctk.CTkLabel(product_frame, text="⚠️ Chưa chọn vật tư cho các hóa đơn.",
                                                     font=("Arial", 12), text_color="#f97316")
                product_summary_label.pack(anchor="w", padx=15, pady=(0, 10))
                def select_grouped():
                    self.open_grouped_product_selection(
                        grouped_products, product_summary_label, selected_products,
                        total_label, payment_label, total_amount, paid_amount
                    )
                ctk.CTkButton(product_frame, text="📝 Chọn vật tư đã sử dụng (gộp)", 
                            fg_color="#f97316", hover_color="#ea580c", height=35,
                            command=select_grouped).pack(anchor="w", padx=15, pady=5)
        else:
            # Một hóa đơn, xử lý như cũ
            invoice_id = invoice_id_list[0]
            db = connect_db()
            require_product_service = None
            require_product_name = None
            if db:
                cursor = db.cursor()
                cursor.execute("SELECT ii.service_id, ii.service_name FROM invoice_items ii WHERE ii.invoice_id = %s", (invoice_id,))
                rows = cursor.fetchall()
                for svc_id, svc_name in rows:
                    cursor.execute("SELECT require_inventory FROM services WHERE id = %s", (svc_id,))
                    res = cursor.fetchone()
                    if res and res[0] == 1:
                        require_product_service = svc_id
                        require_product_name = svc_name
                        break
                cursor.close()
                db.close()
            if require_product_service:
                product_frame = ctk.CTkFrame(form_frame, fg_color="#fff7ed", corner_radius=12,
                                            border_width=1, border_color="#f97316")
                product_frame.pack(fill="x", pady=10)
                ctk.CTkLabel(product_frame, text="📦 VẬT TƯ TIÊU HAO", font=("Arial", 13, "bold"),
                            text_color="#f97316").pack(anchor="w", padx=15, pady=(10, 5))
                product_summary_label = ctk.CTkLabel(product_frame, text="⚠️ Dịch vụ yêu cầu nhập vật tư đã sử dụng",
                                                     font=("Arial", 12), text_color="#f97316")
                product_summary_label.pack(anchor="w", padx=15, pady=(0, 10))
                select_btn = ctk.CTkButton(product_frame, text="📝 Chọn vật tư đã sử dụng",
                                          fg_color="#f97316", hover_color="#ea580c", height=35,
                                          command=lambda: self.open_product_selection(
                                              require_product_service, require_product_name, invoice_id,
                                              lambda prods: self.update_selected_products(prods, product_summary_label, None, selected_products, invoice_id,
                                                                                          payment_label, total_label, total_amount, paid_amount)
                                          ))
                select_btn.pack(anchor="w", padx=15, pady=5)

        ctk.CTkFrame(modal, height=1, fg_color="#e2e8f0").pack(fill="x", padx=40, pady=10)

        # Phương thức thanh toán
        method_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        method_frame.pack(fill="x", pady=15)
        ctk.CTkLabel(method_frame, text="Phương thức thanh toán *", font=("Arial", 13, "bold")).pack(anchor="w")
        self.payment_method = ctk.CTkComboBox(method_frame, values=["Tiền mặt", "Chuyển khoản", "Momo", "ZaloPay"],
                                             height=40, font=("Arial", 13))
        self.payment_method.pack(fill="x", pady=(5, 0))
        self.payment_method.set("Tiền mặt")

        note_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        note_frame.pack(fill="x", pady=15)
        ctk.CTkLabel(note_frame, text="Ghi chú", font=("Arial", 13, "bold")).pack(anchor="w")
        self.note_entry = ctk.CTkEntry(note_frame, height=40, placeholder_text="Nhập ghi chú (nếu có)")
        self.note_entry.pack(fill="x", pady=(5, 0))

        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        ctk.CTkButton(btn_frame, text="Hủy", fg_color="transparent", text_color="#64748b",
                     hover_color="#f1f5f9", height=45, command=modal.destroy).pack(side="left", fill="x", expand=True, padx=5)

        def handle_payment():
            payment_method = self.payment_method.get()
            payment_note = self.note_entry.get()
            temp_id = invoice_id_list if len(invoice_id_list) > 1 else invoice_id_list[0]
            if payment_method in ["Chuyển khoản", "Momo", "ZaloPay"]:
                self.temp_payment_info = {
                    'method': payment_method,
                    'note': payment_note,
                    'invoice_id': temp_id,
                    'total_amount': total_amount,
                    'paid_amount': paid_amount,
                    'default_amount': default_amount,
                    'selected_products': selected_products
                }
                modal.destroy()
                self.show_qr_confirmation_dialog(
                    invoice_display, payment_method, default_amount, payment_note,
                    self.process_payment_from_qr
                )
            else:
                self.process_payment(temp_id, total_amount, paid_amount,
                                     default_amount, modal, selected_products, payment_method, payment_note)

        ctk.CTkButton(btn_frame, text="✅ Xác nhận thanh toán", fg_color="#10b981", hover_color="#059669",
                     height=45, command=handle_payment).pack(side="right", fill="x", expand=True, padx=5)

    def open_grouped_product_selection(self, grouped_products, status_label, selected_products,
                                       total_amount_label, payment_amount_label, total_service_amount, paid_amount):
        """Mở cửa sổ chọn vật tư gộp"""
        def callback(prods, total_product_cost):
            # Cập nhật selected_products
            selected_products.clear()
            selected_products.extend(prods)
            # Cập nhật tổng tiền
            new_total = total_service_amount + total_product_cost
            total_amount_label.configure(text=f"{int(new_total):,} ₫")
            # Số tiền cần thanh toán = new_total - paid_amount
            new_payment = new_total - paid_amount
            payment_amount_label.configure(text=f"{int(new_payment):,} ₫")
            status_label.configure(text=f"✅ Đã chọn {len(prods)} loại vật tư (tổng {int(total_product_cost):,}₫)", text_color="#10b981")

        GroupedProductSelectionWindow(self, grouped_products, callback, total_service_amount, paid_amount,
                                      total_amount_label, payment_amount_label)

    def update_selected_products(self, products, status_label, select_btn, selected_products, invoice_id,
                                 payment_label, total_label, total_service_amount, paid_amount):
        # Lưu ý: products là list các dict (id, name, quantity, price, unit)
        # Tính lại tổng tiền vật tư
        old_products = [p for p in selected_products if p.get('invoice_id') == invoice_id]
        old_cost = sum(p["quantity"] * p["price"] for p in old_products)
        # Loại bỏ các sản phẩm cũ của invoice này
        selected_products[:] = [p for p in selected_products if p.get('invoice_id') != invoice_id]
        for p in products:
            p['invoice_id'] = invoice_id
            selected_products.append(p)
        new_cost = sum(p["quantity"] * p["price"] for p in products)
        cost_diff = new_cost - old_cost
        new_total = total_service_amount + cost_diff
        total_label.configure(text=f"{int(new_total):,} ₫")
        new_payment = new_total - paid_amount
        payment_label.configure(text=f"{int(new_payment):,} ₫")
        status_label.configure(text=f"✅ Đã chọn {len(products)} vật tư (tổng {int(new_cost):,}₫)", text_color="#10b981")
        if select_btn:
            select_btn.configure(fg_color="#10b981", text="🔄 Thay đổi vật tư")

    def process_payment_from_qr(self):
        if hasattr(self, 'temp_payment_info'):
            info = self.temp_payment_info
            self.process_payment(
                info['invoice_id'],
                info['total_amount'],
                info['paid_amount'],
                info['default_amount'],
                None,
                info['selected_products'],
                info['method'],
                info['note']
            )
            del self.temp_payment_info

    def process_payment(self, invoice_id, total_amount, paid_amount, payment_amount, modal, selected_products, payment_method=None, note=None):
        if payment_method is None:
            payment_method = self.payment_method.get()
        if note is None:
            note = self.note_entry.get()

        if payment_method in ["Chuyển khoản", "Momo", "ZaloPay"]:
            if not messagebox.askyesno("Xác nhận", f"Bạn đã chuyển khoản thành công qua {payment_method}?\nHãy xác nhận sau khi hoàn tất giao dịch!"):
                return

        db = connect_db()
        if not db:
            messagebox.showerror("Lỗi", "Không thể kết nối database!")
            return
        cursor = db.cursor()
        try:
            invoice_ids = invoice_id if isinstance(invoice_id, list) else [invoice_id]
            total_product_cost = 0

            # Xử lý vật tư
            for prod in selected_products:
                # Nếu có 'invoices_needs' (từ gộp) thì phân bổ
                if 'invoices_needs' in prod:
                    needs = prod['invoices_needs']
                    total_needed = sum(needs.values())
                    if total_needed == 0:
                        continue
                    remaining_qty = prod['quantity']
                    # Phân bổ tỷ lệ theo nhu cầu
                    for inv_id, need in needs.items():
                        if remaining_qty <= 0:
                            break
                        if need == 0:
                            continue
                        assign = int(need / total_needed * prod['quantity'])
                        if assign > remaining_qty:
                            assign = remaining_qty
                        if assign > 0:
                            cursor.execute("SELECT id FROM invoice_products WHERE invoice_id = %s AND product_id = %s", (inv_id, prod['id']))
                            existing = cursor.fetchone()
                            if existing:
                                cursor.execute("UPDATE invoice_products SET quantity = quantity + %s WHERE invoice_id = %s AND product_id = %s",
                                               (assign, inv_id, prod['id']))
                            else:
                                cursor.execute("INSERT INTO invoice_products (invoice_id, product_id, product_name, quantity, price) VALUES (%s, %s, %s, %s, %s)",
                                               (inv_id, prod['id'], prod['name'], assign, prod['price']))
                            remaining_qty -= assign
                    if remaining_qty > 0 and needs:
                        first_inv = list(needs.keys())[0]
                        cursor.execute("UPDATE invoice_products SET quantity = quantity + %s WHERE invoice_id = %s AND product_id = %s",
                                       (remaining_qty, first_inv, prod['id']))
                    # Trừ kho tổng
                    cursor.execute("UPDATE inventory SET stock_quantity = stock_quantity - %s WHERE id = %s AND stock_quantity >= %s",
                                   (prod['quantity'], prod['id'], prod['quantity']))
                    if cursor.rowcount == 0:
                        raise Exception(f"Không đủ tồn kho cho {prod['name']}!")
                    total_product_cost += prod['quantity'] * prod['price']
                else:
                    # Sản phẩm của một invoice
                    inv_id = prod.get('invoice_id', invoice_ids[0] if len(invoice_ids) == 1 else None)
                    if inv_id is None:
                        raise Exception("Không thể xác định hóa đơn cho vật tư.")
                    cursor.execute("SELECT id FROM invoice_products WHERE invoice_id = %s AND product_id = %s", (inv_id, prod['id']))
                    existing = cursor.fetchone()
                    if existing:
                        cursor.execute("UPDATE invoice_products SET quantity = %s, price = %s WHERE invoice_id = %s AND product_id = %s",
                                       (prod['quantity'], prod['price'], inv_id, prod['id']))
                    else:
                        cursor.execute("INSERT INTO invoice_products (invoice_id, product_id, product_name, quantity, price) VALUES (%s, %s, %s, %s, %s)",
                                       (inv_id, prod['id'], prod['name'], prod['quantity'], prod['price']))
                    cursor.execute("UPDATE inventory SET stock_quantity = stock_quantity - %s WHERE id = %s AND stock_quantity >= %s",
                                   (prod['quantity'], prod['id'], prod['quantity']))
                    if cursor.rowcount == 0:
                        raise Exception(f"Không đủ tồn kho cho {prod['name']}!")
                    total_product_cost += prod['quantity'] * prod['price']

            cursor.execute("SHOW COLUMNS FROM payments LIKE 'note'")
            has_note = cursor.fetchone() is not None

            remaining_amount = float(payment_amount)
            if remaining_amount <= 0:
                raise Exception("Số tiền thanh toán không hợp lệ.")

            # Lấy danh sách invoices theo thứ tự
            placeholders = ','.join(['%s'] * len(invoice_ids))
            cursor.execute(f"SELECT id, total_amount, COALESCE((SELECT SUM(amount) FROM payments WHERE invoice_id = i.id), 0) as paid_amount FROM invoices i WHERE id IN ({placeholders}) ORDER BY created_at ASC", tuple(invoice_ids))
            invoices_to_update = cursor.fetchall()

            for inv in invoices_to_update:
                inv_id, inv_total, inv_paid = inv
                inv_total = float(inv_total or 0)
                inv_paid = float(inv_paid or 0)
                inv_need = inv_total - inv_paid
                if inv_need <= 0:
                    continue
                pay_piece = min(inv_need, remaining_amount)
                if pay_piece <= 0:
                    break
                if has_note:
                    cursor.execute("INSERT INTO payments (invoice_id, amount, payment_method, payment_date, note) VALUES (%s, %s, %s, NOW(), %s)",
                                   (inv_id, pay_piece, payment_method, note))
                else:
                    cursor.execute("INSERT INTO payments (invoice_id, amount, payment_method, payment_date) VALUES (%s, %s, %s, NOW())",
                                   (inv_id, pay_piece, payment_method))
                new_paid = inv_paid + pay_piece
                new_status = "Đã thanh toán" if new_paid >= inv_total else "Thanh toán một phần"
                cursor.execute("UPDATE invoices SET status = %s WHERE id = %s", (new_status, inv_id))
                remaining_amount -= pay_piece

            db.commit()
            paid_amount += float(payment_amount) - remaining_amount
            remaining_new = total_amount - paid_amount
            msg = f"✅ Đã thanh toán {int(payment_amount - remaining_amount):,} ₫ thành công!\n"
            if selected_products and len(invoice_ids) == 1:
                msg += f"📦 Đã trừ kho {len(selected_products)} loại vật tư (trị giá {int(total_product_cost):,} ₫)\n"
            if remaining_new <= 0:
                msg += "🎉 Đã thanh toán hoàn tất tất cả hóa đơn!"
            else:
                msg += f"📌 Số tiền còn lại cần thanh toán: {int(remaining_new):,} ₫"
            messagebox.showinfo("Thành công", msg)
            if modal is not None:
                modal.destroy()
            self.load_invoices()
            if hasattr(self.parent_app, 'refresh_dashboard'):
                self.parent_app.refresh_dashboard()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", f"Không thể thanh toán: {e}")
        finally:
            db.close()

    def show_payment_history(self):
        history_window = ctk.CTkToplevel(self)
        history_window.title("Lịch sử thanh toán")
        history_window.geometry("1200x600")
        history_window.attributes("-topmost", True)
        history_window.grab_set()
        history_window.configure(fg_color="white")
        header_frame = ctk.CTkFrame(history_window, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header_frame, text="📜 Lịch sử thanh toán", font=("Arial", 24, "bold"), text_color="#1e293b").pack(side="left")
        search_frame = ctk.CTkFrame(history_window, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        search_frame.pack(fill="x", padx=20, pady=(0, 15))
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Tìm kiếm theo mã hóa đơn, khách hàng...", border_width=0, fg_color="transparent", height=40)
        search_entry.pack(fill="x", padx=15)
        table_frame = ctk.CTkFrame(history_window, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        headers = ["Mã HĐ", "Khách hàng", "Biển số", "Tổng tiền", "Đã thanh toán", "Ngày thanh toán", "Phương thức", "Vật tư", "Ghi chú"]
        header_frame = ctk.CTkFrame(table_frame, fg_color="#f1f5f9", height=40)
        header_frame.pack(fill="x", padx=1, pady=(1, 0))
        for i, text in enumerate(headers):
            ctk.CTkLabel(header_frame, text=text, font=("Arial", 12, "bold"), text_color="#64748b").grid(row=0, column=i, padx=10, pady=10, sticky="w")
            header_frame.grid_columnconfigure(i, weight=1)
        scroll_frame = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        db = connect_db()
        if db:
            cursor = db.cursor()
            def load_history(*args):
                for w in scroll_frame.winfo_children(): w.destroy()
                search = f"%{search_entry.get()}%"
                query = """
                    SELECT i.id, c.full_name, a.car_plate, i.total_amount, p.amount as paid_amount,
                           p.payment_date, p.payment_method, p.note,
                           (SELECT COUNT(*) FROM invoice_products WHERE invoice_id = i.id) as product_count
                    FROM payments p
                    JOIN invoices i ON p.invoice_id = i.id
                    JOIN customers c ON i.customer_id = c.id
                    LEFT JOIN appointments a ON i.appointment_id = a.id
                    WHERE c.full_name LIKE %s OR c.phone LIKE %s OR CAST(i.id AS CHAR) LIKE %s
                    ORDER BY p.payment_date DESC
                """
                cursor.execute(query, (search, search, search))
                payments = cursor.fetchall()
                if not payments:
                    ctk.CTkLabel(scroll_frame, text="📭 Không có dữ liệu thanh toán", font=("Arial", 14), text_color="#64748b").pack(pady=50)
                    return
                for idx, pay in enumerate(payments):
                    row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent", height=35)
                    row_frame.pack(fill="x", pady=2)
                    ctk.CTkLabel(row_frame, text=f"HD{pay[0]:04d}", font=("Arial", 12), text_color="#2563eb").grid(row=0, column=0, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=pay[1], font=("Arial", 12)).grid(row=0, column=1, padx=10, pady=8, sticky="w")
                    car_plate = pay[2] if pay[2] else "---"
                    ctk.CTkLabel(row_frame, text=car_plate, font=("Arial", 12)).grid(row=0, column=2, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=f"{int(pay[3]):,} ₫", font=("Arial", 12)).grid(row=0, column=3, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=f"{int(pay[4]):,} ₫", font=("Arial", 12, "bold"), text_color="#10b981").grid(row=0, column=4, padx=10, pady=8, sticky="w")
                    date_str = pay[5].strftime("%d/%m/%Y %H:%M") if pay[5] else ""
                    ctk.CTkLabel(row_frame, text=date_str, font=("Arial", 11)).grid(row=0, column=5, padx=10, pady=8, sticky="w")
                    method_color = "#3b82f6" if pay[6] == "Chuyển khoản" else "#10b981" if pay[6] == "Tiền mặt" else "#8b5cf6"
                    ctk.CTkLabel(row_frame, text=pay[6], font=("Arial", 11, "bold"), text_color=method_color).grid(row=0, column=6, padx=10, pady=8, sticky="w")
                    product_text = f"{pay[8]} loại" if pay[8] > 0 else "Không"
                    product_color = "#10b981" if pay[8] > 0 else "#64748b"
                    ctk.CTkLabel(row_frame, text=product_text, font=("Arial", 11), text_color=product_color).grid(row=0, column=7, padx=10, pady=8, sticky="w")
                    note = pay[7] if pay[7] else "---"
                    ctk.CTkLabel(row_frame, text=note, font=("Arial", 11), text_color="#64748b").grid(row=0, column=8, padx=10, pady=8, sticky="w")
                    if idx < len(payments) - 1:
                        ctk.CTkFrame(scroll_frame, height=1, fg_color="#e2e8f0").pack(fill="x", padx=10)
            search_entry.bind("<KeyRelease>", lambda e: load_history())
            load_history()
            db.close()


if __name__ == "__main__":
    pass