import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from tkcalendar import DateEntry
import re
from database import connect_db


class ServiceSelectionWindow(ctk.CTkToplevel):
    """Cửa sổ xác nhận dịch vụ sử dụng (hỗ trợ nhiều dịch vụ)"""
    def __init__(self, parent, appointment_id, callback):
        super().__init__(parent)
        self.appointment_id = appointment_id
        self.callback = callback
        self.selected_services = []
        
        self.title("Xác nhận dịch vụ sử dụng")
        self.geometry("650x500")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="white")
        
        ctk.CTkLabel(self, text="XÁC NHẬN DỊCH VỤ SỬ DỤNG", font=("Arial", 20, "bold"),
                    text_color="#1e293b").pack(pady=20)
        ctk.CTkLabel(self, text="Chỉnh sửa hoặc xóa các dịch vụ không sử dụng",
                    font=("Arial", 12), text_color="#64748b").pack(pady=(0, 15))
        
        self.services_frame = ctk.CTkScrollableFrame(self, fg_color="#f8fafc", corner_radius=10)
        self.services_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.service_entries = {}
        self.load_appointment_services()
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Hủy", fg_color="transparent", text_color="#64748b",
                     height=40, command=self.destroy).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="✅ Xác nhận hoàn thành", fg_color="#10b981", hover_color="#059669",
                     height=40, command=self.confirm_services).pack(side="right", fill="x", expand=True, padx=5)
    
    def load_appointment_services(self):
        db = connect_db()
        if not db:
            ctk.CTkLabel(self.services_frame, text="Lỗi kết nối database!",
                        font=("Arial", 12), text_color="#ef4444").pack(pady=20)
            return
        cursor = db.cursor()
        cursor.execute("""
            SELECT s.id, s.service_name, s.price
            FROM appointment_services app_s
            JOIN services s ON app_s.service_id = s.id
            WHERE app_s.appointment_id = %s
        """, (self.appointment_id,))
        services_data = cursor.fetchall()
        db.close()
        
        if not services_data:
            ctk.CTkLabel(self.services_frame, text="Lịch hẹn này không có dịch vụ nào!",
                        font=("Arial", 12), text_color="#64748b").pack(pady=20)
            return
        
        for service_id, service_name, price in services_data:
            self.create_service_card(service_id, service_name, price)
        
        add_btn = ctk.CTkButton(self.services_frame, text="+ Thêm dịch vụ", 
                               fg_color="#3b82f6", hover_color="#2563eb",
                               height=40, command=self.add_service)
        add_btn.pack(pady=10)
    
    def create_service_card(self, service_id, service_name, price):
        card = ctk.CTkFrame(self.services_frame, fg_color="white", corner_radius=10,
                           border_width=1, border_color="#e2e8f0")
        card.pack(fill="x", pady=8, padx=5)
        
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        ctk.CTkLabel(left, text=service_name, font=("Arial", 14, "bold"),
                    text_color="#1e293b").pack(anchor="w")
        ctk.CTkLabel(left, text=f"Giá: {int(price):,} ₫", font=("Arial", 12),
                    text_color="#10b981").pack(anchor="w")
        
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=15, pady=10)
        var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(right, text="Sử dụng", variable=var, font=("Arial", 12)).pack(side="left", padx=5)
        
        def view_details():
            ServiceDetailsModal(self, self.appointment_id, service_id, service_name, price)
        detail_btn = ctk.CTkButton(right, text="👁️ Chi tiết", width=80, height=30, 
                                  fg_color="#f59e0b", command=view_details)
        detail_btn.pack(side="left", padx=5)
        
        def delete_service():
            if messagebox.askyesno("Xác nhận", f"Xóa dịch vụ '{service_name}'?"):
                db = connect_db()
                if db:
                    cursor = db.cursor()
                    cursor.execute("DELETE FROM appointment_services WHERE appointment_id = %s AND service_id = %s", 
                                 (self.appointment_id, service_id))
                    db.commit()
                    db.close()
                card.destroy()
                del self.service_entries[service_id]
        del_btn = ctk.CTkButton(right, text="🗑️ Xóa", width=60, height=30, 
                               fg_color="#ef4444", command=delete_service)
        del_btn.pack(side="left", padx=5)
        
        self.service_entries[service_id] = {'name': service_name, 'price': price, 'var': var, 'card': card}
    
    def add_service(self):
        """Thêm dịch vụ mới - sử dụng class ServiceSelectionModal có sẵn trong file"""
        def on_service_selected(selected_service):
            if selected_service:
                service_id = selected_service['id']
                service_name = selected_service['name']
                price = selected_service['price']
                
                db = connect_db()
                if db:
                    cursor = db.cursor()
                    cursor.execute("""
                        INSERT IGNORE INTO appointment_services (appointment_id, service_id)
                        VALUES (%s, %s)
                    """, (self.appointment_id, service_id))
                    db.commit()
                    db.close()
                self.create_service_card(service_id, service_name, price)
        
        modal = ServiceSelectionModal(self, on_service_selected)
    
    def confirm_services(self):
        self.selected_services = []
        for sid, data in self.service_entries.items():
            if data['var'].get():
                self.selected_services.append({'service_id': sid, 'service_name': data['name'], 'price': data['price']})
        if not self.selected_services:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ít nhất 1 dịch vụ!")
            return
        self.destroy()
        if self.callback:
            self.callback(self.selected_services)


class AppointmentFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#f3f4f6")
        self.parent_app = master
        self.selected_services_for_appointment = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=15)
        ctk.CTkLabel(header, text="Lịch hẹn", font=("Arial", 24, "bold")).pack(side="left")
        history_btn = ctk.CTkButton(header, text="📜 Lịch sử bàn giao", fg_color="#8b5cf6", command=self.show_handover_history)
        history_btn.pack(side="right", padx=5)
        ctk.CTkButton(header, text="+ Tạo lịch hẹn", fg_color="#2563eb", command=self.open_modal).pack(side="right", padx=5)

        self.search = ctk.CTkEntry(self, placeholder_text="🔍 Tìm khách / biển số...")
        self.search.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 10))
        self.search.bind("<KeyRelease>", lambda e: self.load())

        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 20))

        self.init_appointment_services_table()
        self.load()

    def init_appointment_services_table(self):
        db = connect_db()
        if not db: return
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointment_services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                appointment_id INT NOT NULL,
                service_id INT NOT NULL,
                FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
                FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
                UNIQUE KEY unique_appointment_service (appointment_id, service_id)
            )
        """)
        cursor.execute("""
            INSERT IGNORE INTO appointment_services (appointment_id, service_id)
            SELECT id, service_id FROM appointments WHERE service_id IS NOT NULL
        """)
        db.commit()
        db.close()

    def load(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        db = connect_db()
        if not db: return
        cursor = db.cursor()
        search = f"%{self.search.get()}%"
        cursor.execute("""
            SELECT a.id, c.full_name, a.car_plate,
                   GROUP_CONCAT(s.service_name SEPARATOR '\n') AS services,
                   a.appointment_date, a.status,
                   SUM(s.price) AS total_price
            FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            LEFT JOIN appointment_services app_s ON a.id = app_s.appointment_id
            LEFT JOIN services s ON app_s.service_id = s.id
            WHERE (c.full_name LIKE %s OR a.car_plate LIKE %s)
            AND a.status NOT IN ('Đã bàn giao', 'Hủy lịch')
            GROUP BY a.id
            ORDER BY a.appointment_date DESC
        """, (search, search))
        appointments = cursor.fetchall()
        db.close()
        if not appointments:
            empty_label = ctk.CTkLabel(self.list_frame, text="📭 Không có lịch hẹn nào đang hoạt động",
                                      font=("Arial", 14), text_color="#64748b")
            empty_label.pack(pady=50)
        else:
            for row in appointments:
                self.card(row)

    def show_handover_history(self):
        history_window = ctk.CTkToplevel(self)
        history_window.title("Lịch sử bàn giao")
        history_window.geometry("900x500")
        history_window.attributes("-topmost", True)
        history_window.grab_set()
        history_window.configure(fg_color="white")
        header_frame = ctk.CTkFrame(history_window, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20,10))
        ctk.CTkLabel(header_frame, text="📜 LỊCH SỬ BÀN GIAO", font=("Arial",20,"bold"), text_color="#1e293b").pack(side="left")
        search_frame = ctk.CTkFrame(history_window, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        search_frame.pack(fill="x", padx=20, pady=(0,15))
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Tìm kiếm...", border_width=0, fg_color="transparent", height=40)
        search_entry.pack(fill="x", padx=15)
        table_frame = ctk.CTkFrame(history_window, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0,20))
        headers = ["Mã LH","Khách hàng","Biển số","Dịch vụ","Ngày hẹn","Giá","Trạng thái"]
        header_frame2 = ctk.CTkFrame(table_frame, fg_color="#f1f5f9", height=40)
        header_frame2.pack(fill="x", padx=1, pady=(1,0))
        for i,text in enumerate(headers):
            ctk.CTkLabel(header_frame2, text=text, font=("Arial",12,"bold"), text_color="#64748b").grid(row=0,column=i,padx=10,pady=10,sticky="w")
            header_frame2.grid_columnconfigure(i, weight=1)
        scroll_frame = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        db = connect_db()
        if db:
            cursor = db.cursor()
            def load_history(*args):
                for w in scroll_frame.winfo_children(): w.destroy()
                search = f"%{search_entry.get()}%"
                cursor.execute("""
                    SELECT a.id, c.full_name, a.car_plate,
                           GROUP_CONCAT(s.service_name SEPARATOR ', ') AS services,
                           a.appointment_date, SUM(s.price) AS total_price, a.status
                    FROM appointments a
                    JOIN customers c ON a.customer_id = c.id
                    LEFT JOIN appointment_services app_s ON a.id = app_s.appointment_id
                    LEFT JOIN services s ON app_s.service_id = s.id
                    WHERE (c.full_name LIKE %s OR a.car_plate LIKE %s)
                    AND a.status = 'Đã bàn giao'
                    GROUP BY a.id
                    ORDER BY a.appointment_date DESC
                """, (search, search))
                appts = cursor.fetchall()
                if not appts:
                    ctk.CTkLabel(scroll_frame, text="📭 Không có dữ liệu", font=("Arial",14), text_color="#64748b").pack(pady=50)
                    return
                for idx,appt in enumerate(appts):
                    row = ctk.CTkFrame(scroll_frame, fg_color="transparent", height=35)
                    row.pack(fill="x", pady=2)
                    dt = appt[4]
                    if isinstance(dt, str): dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    ctk.CTkLabel(row, text=f"AP{appt[0]:04d}", font=("Arial",12), text_color="#2563eb").grid(row=0,column=0,padx=10,pady=8,sticky="w")
                    ctk.CTkLabel(row, text=appt[1], font=("Arial",12)).grid(row=0,column=1,padx=10,pady=8,sticky="w")
                    ctk.CTkLabel(row, text=appt[2], font=("Arial",12)).grid(row=0,column=2,padx=10,pady=8,sticky="w")
                    ctk.CTkLabel(row, text=appt[3], font=("Arial",11)).grid(row=0,column=3,padx=10,pady=8,sticky="w")
                    ctk.CTkLabel(row, text=dt.strftime("%d/%m/%Y %H:%M"), font=("Arial",11)).grid(row=0,column=4,padx=10,pady=8,sticky="w")
                    ctk.CTkLabel(row, text=f"{int(appt[5]):,} đ" if appt[5] else "0 đ", font=("Arial",11,"bold"), text_color="#10b981").grid(row=0,column=5,padx=10,pady=8,sticky="w")
                    ctk.CTkLabel(row, text="✅ Đã bàn giao", font=("Arial",11), text_color="#10b981").grid(row=0,column=6,padx=10,pady=8,sticky="w")
                    if idx < len(appts)-1:
                        ctk.CTkFrame(scroll_frame, height=1, fg_color="#e2e8f0").pack(fill="x", padx=10)
            search_entry.bind("<KeyRelease>", lambda e: load_history())
            load_history()
            db.close()

    def card(self, appt):
        appt_id, customer_name, plate, services_str, dt, status, total_price = appt
        card = ctk.CTkFrame(self.list_frame, fg_color="white", corner_radius=12, border_width=1)
        card.pack(fill="x", pady=8, padx=5)
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        if services_str:
            for svc in services_str.split('\n'):
                ctk.CTkLabel(left, text=f"• {svc}", font=("Arial",14)).pack(anchor="w")
        else:
            ctk.CTkLabel(left, text="(Chưa có dịch vụ)", font=("Arial",14,"italic"), text_color="#ef4444").pack(anchor="w")
        ctk.CTkLabel(left, text=f"{customer_name} • {plate}", text_color="#6b7280").pack(anchor="w")
        status_color = {"Chờ xác nhận":"#facc15","Đã xác nhận":"#60a5fa","Đã hoàn thành":"#22c55e"}.get(status,"#e5e7eb")
        ctk.CTkLabel(left, text=status, fg_color=status_color, corner_radius=6, padx=10).pack(anchor="w", pady=5)
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=15, pady=10)
        if isinstance(dt, str): dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        ctk.CTkLabel(right, text=dt.strftime("%d/%m/%Y")).pack(anchor="e")
        ctk.CTkLabel(right, text=dt.strftime("%H:%M")).pack(anchor="e")
        if total_price:
            ctk.CTkLabel(right, text=f"{int(total_price):,} đ", font=("Arial",12,"bold"), text_color="#10b981").pack(anchor="e", pady=2)
        btn = ctk.CTkFrame(right, fg_color="transparent")
        btn.pack(anchor="e", pady=5)
        if status == "Chờ xác nhận":
            ctk.CTkButton(btn, text="Xác nhận", command=lambda: self.update_status(appt_id, "Đã xác nhận")).pack(side="left", padx=3)
            ctk.CTkButton(btn, text="Hủy", fg_color="#ef4444", command=lambda: self.update_status(appt_id, "Hủy lịch")).pack(side="left", padx=3)
        elif status == "Đã xác nhận":
            ctk.CTkButton(btn, text="Hoàn thành", fg_color="#10b981", command=lambda: self.complete_appointment(appt_id)).pack(side="left")
        elif status == "Đã hoàn thành":
            ctk.CTkButton(btn, text="Bàn giao", fg_color="#2563eb", command=lambda: self.handover_appointment(appt_id)).pack(side="left")

    def update_status(self, appt_id, status):
        db = connect_db()
        if not db: return
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE appointments SET status=%s WHERE id=%s", (status, appt_id))
            db.commit()
            messagebox.showinfo("Thành công", f"Đã {status.lower()} lịch hẹn!")
            self.load()
            if hasattr(self.parent_app, 'refresh_dashboard'): self.parent_app.refresh_dashboard()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", str(e))
        finally:
            db.close()

    def complete_appointment(self, appt_id):
        def on_services_confirmed(selected_services):
            self.selected_services_for_appointment[appt_id] = selected_services
            db = connect_db()
            if db:
                cursor = db.cursor()
                cursor.execute("UPDATE appointments SET status='Đã hoàn thành', progress_percent=100 WHERE id=%s", (appt_id,))
                db.commit()
                db.close()
                messagebox.showinfo("Thành công", "Đã hoàn thành dịch vụ!\nNhấn 'Bàn giao' để tạo hóa đơn.")
                self.load()
                if hasattr(self.parent_app, 'refresh_dashboard'): self.parent_app.refresh_dashboard()
        ServiceSelectionWindow(self, appt_id, on_services_confirmed)

    def handover_appointment(self, appt_id):
        if not messagebox.askyesno("Xác nhận", "Bàn giao xe và tạo hóa đơn?"):
            return
        db = connect_db()
        if not db:
            messagebox.showerror("Lỗi", "Không kết nối DB!")
            return
        cursor = db.cursor()
        try:
            cursor.execute("SELECT customer_id, car_plate FROM appointments WHERE id=%s", (appt_id,))
            appt_info = cursor.fetchone()
            if not appt_info:
                messagebox.showerror("Lỗi", "Không tìm thấy lịch hẹn!")
                return
            customer_id, car_plate = appt_info
            cursor.execute("""
                SELECT s.id, s.service_name, s.price
                FROM appointment_services app_s
                JOIN services s ON app_s.service_id = s.id
                WHERE app_s.appointment_id = %s
            """, (appt_id,))
            services = cursor.fetchall()
            if not services:
                messagebox.showerror("Lỗi", "Lịch hẹn không có dịch vụ nào!")
                return
            total = sum(price for _, _, price in services)
            cursor.execute("SELECT id, status FROM invoices WHERE appointment_id=%s", (appt_id,))
            existing = cursor.fetchone()
            if existing:
                inv_id, inv_status = existing
                if inv_status == "Đã thanh toán":
                    cursor.execute("UPDATE appointments SET status='Đã bàn giao' WHERE id=%s", (appt_id,))
                    db.commit()
                    messagebox.showinfo("Thông báo", "Hóa đơn đã thanh toán trước đó!")
                else:
                    cursor.execute("UPDATE appointments SET status='Đã bàn giao' WHERE id=%s", (appt_id,))
                    db.commit()
                    messagebox.showinfo("Thành công", "Đã cập nhật bàn giao!")
            else:
                cursor.execute("""
                    INSERT INTO invoices (appointment_id, customer_id, total_amount, status, created_at)
                    VALUES (%s, %s, %s, 'Chưa thanh toán', NOW())
                """, (appt_id, customer_id, total))
                inv_id = cursor.lastrowid
                for sid, sname, sprice in services:
                    cursor.execute("""
                        INSERT INTO invoice_items (invoice_id, service_id, service_name, price, quantity)
                        VALUES (%s, %s, %s, %s, 1)
                    """, (inv_id, sid, sname, sprice))
                # Bổ sung: copy vật tư từ appointment_materials sang invoice_products
                cursor.execute("""
                    SELECT am.product_id, p.product_name, SUM(am.quantity_used) as total_qty, p.unit, p.price
                    FROM appointment_materials am
                    LEFT JOIN inventory p ON am.product_id = p.id
                    WHERE am.appointment_id = %s
                    GROUP BY am.product_id, p.product_name, p.unit, p.price
                """, (appt_id,))
                materials = cursor.fetchall()
                for mat in materials:
                    if mat[0] is not None:
                        qty = float(mat[2]) if mat[2] is not None else 0
                        price = float(mat[4]) if mat[4] is not None else 0
                        cursor.execute("""
                            INSERT INTO invoice_products (invoice_id, product_id, product_name, quantity, price)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (inv_id, mat[0], mat[1], qty, price))
                cursor.execute("UPDATE appointments SET status='Đã bàn giao' WHERE id=%s", (appt_id,))
                db.commit()
                messagebox.showinfo("Thành công", f"Đã tạo hóa đơn HD{inv_id:04d}!")
            if appt_id in self.selected_services_for_appointment:
                del self.selected_services_for_appointment[appt_id]
            self.load()
            if hasattr(self.parent_app, 'show_payment_tab'): self.parent_app.show_payment_tab()
            if hasattr(self.parent_app, 'refresh_dashboard'): self.parent_app.refresh_dashboard()
            if hasattr(self.parent_app, 'refresh_payments'): self.parent_app.refresh_payments()
        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", str(e))
        finally:
            db.close()

    def open_modal(self):
        self.modal_window = ctk.CTkToplevel(self)
        self.modal_window.title("Tạo Lịch Hẹn Mới")
        self.modal_window.geometry("650x900")
        self.modal_window.attributes("-topmost", True)
        self.modal_window.grab_set()
        self.modal_window.grid_columnconfigure(0, weight=1)
        self.modal_window.grid_rowconfigure(0, weight=1)

        main_scroll = ctk.CTkScrollableFrame(self.modal_window, fg_color="transparent")
        main_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main_scroll, text="THÔNG TIN KHÁCH HÀNG", font=("Arial",15,"bold"), text_color="#2563eb").grid(row=0,column=0,sticky="w",pady=(10,15))
        self.ent_name = self.create_input_group(main_scroll, "Họ và tên *:", "Nhập tên khách hàng", 1)
        self.ent_phone = self.create_input_group(main_scroll, "Số điện thoại *:", "VD: 0912345678", 3)
        self.ent_email = self.create_input_group(main_scroll, "Email:", "VD: example@email.com", 5)

        ctk.CTkLabel(main_scroll, text="THÔNG TIN XE", font=("Arial",15,"bold"), text_color="#2563eb").grid(row=7,column=0,sticky="w",pady=(10,15))
        self.ent_plate = self.create_input_group(main_scroll, "Biển số xe *:", "VD: 30A-123.45", 8)
        self.ent_brand = self.create_input_group(main_scroll, "Hãng xe:", "VD: Toyota, Honda...", 10)
        self.ent_model = self.create_input_group(main_scroll, "Mẫu xe:", "VD: Vios, Civic...", 12)
        self.ent_year = self.create_input_group(main_scroll, "Năm sản xuất:", "VD: 2020", 14)

        ctk.CTkLabel(main_scroll, text="CHỌN DỊCH VỤ", font=("Arial",15,"bold"), text_color="#2563eb").grid(row=16,column=0,sticky="w",pady=(10,5))
        svc_frame = ctk.CTkFrame(main_scroll, fg_color="#f8fafc", border_width=1, border_color="#e2e8f0")
        svc_frame.grid(row=17, column=0, sticky="ew", pady=5)
        svc_scroll = ctk.CTkScrollableFrame(svc_frame, height=150, fg_color="transparent")
        svc_scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, service_name, price FROM services WHERE status = 1")
        services = cursor.fetchall()
        db.close()

        self.svc_vars = {}
        self.svc_prices = {}
        count_label = ctk.CTkLabel(main_scroll, text="Đã chọn: 0 dịch vụ", font=("Arial",11,"italic"), text_color="#64748b")
        count_label.grid(row=18, column=0, sticky="e")
        def update_count(*args):
            count = sum(v.get() for v in self.svc_vars.values())
            count_label.configure(text=f"Đã chọn: {count} dịch vụ")
            total = sum(self.svc_prices[sid] for sid, v in self.svc_vars.items() if v.get())
            self.total_label.configure(text=f"Tổng tiền: {int(total):,} đ")
        for sid, name_svc, price in services:
            var = ctk.BooleanVar()
            var.trace_add("write", update_count)
            frame = ctk.CTkFrame(svc_scroll, fg_color="transparent")
            frame.pack(fill="x", pady=4, padx=10)
            ctk.CTkCheckBox(frame, text=name_svc, variable=var, font=("Arial",13)).pack(side="left")
            ctk.CTkLabel(frame, text=f"{int(price):,} đ", font=("Arial",11), text_color="#10b981").pack(side="right")
            self.svc_vars[sid] = var
            self.svc_prices[sid] = price

        ctk.CTkLabel(main_scroll, text="THỜI GIAN HẸN", font=("Arial",15,"bold"), text_color="#2563eb").grid(row=19,column=0,sticky="w",pady=(20,5))
        time_container = ctk.CTkFrame(main_scroll, fg_color="transparent")
        time_container.grid(row=20, column=0, sticky="ew")
        time_container.grid_columnconfigure((0,1), weight=1)
        ctk.CTkLabel(time_container, text="Ngày hẹn:", font=("Arial",12)).grid(row=0,column=0,sticky="w")
        self.date_pick = DateEntry(time_container, date_pattern="yyyy-mm-dd", background='#2563eb', foreground='white')
        self.date_pick.grid(row=1, column=0, sticky="ew", padx=(0,10), pady=2)
        ctk.CTkLabel(time_container, text="Giờ hẹn (HH:MM):", font=("Arial",12)).grid(row=0,column=1,sticky="w")
        self.time_ent = ctk.CTkEntry(time_container, placeholder_text="08:30", height=35)
        self.time_ent.grid(row=1, column=1, sticky="ew", pady=2)

        self.total_label = ctk.CTkLabel(main_scroll, text="Tổng tiền: 0 đ", font=("Arial",14,"bold"), text_color="#ef4444")
        self.total_label.grid(row=21, column=0, sticky="e", pady=(10,0))
        btn_save = ctk.CTkButton(main_scroll, text="XÁC NHẬN TẠO LỊCH", font=("Arial",14,"bold"), fg_color="#2563eb", height=50, command=self.save_appointment)
        btn_save.grid(row=22, column=0, sticky="ew", pady=30)

    def create_input_group(self, parent, label_text, placeholder, row):
        ctk.CTkLabel(parent, text=label_text, font=("Arial",12)).grid(row=row, column=0, sticky="w")
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=35)
        entry.grid(row=row+1, column=0, sticky="ew", pady=(2,12))
        return entry

    def save_appointment(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()
        plate = self.ent_plate.get().strip().upper()
        brand = self.ent_brand.get().strip()
        model = self.ent_model.get().strip()
        year_str = self.ent_year.get().strip()
        selected_services = [sid for sid, v in self.svc_vars.items() if v.get()]

        if not name or not phone or not plate:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin bắt buộc!")
            return
        if not selected_services:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 dịch vụ!")
            return
        if not phone.isdigit() or len(phone) < 9:
            messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ!")
            return

        current_year = datetime.now().year
        year = None
        if year_str:
            if not year_str.isdigit():
                messagebox.showerror("Lỗi", "Năm sản xuất phải là số!")
                return
            year = int(year_str)
            if year < 1900 or year > current_year + 1:
                messagebox.showerror("Lỗi", f"Năm sản xuất không hợp lệ (1900-{current_year})!")
                return

        try:
            dt_str = self.date_pick.get() + " " + self.time_ent.get()
            appointment_date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except:
            messagebox.showerror("Lỗi", "Ngày/giờ không hợp lệ!")
            return

        db = connect_db()
        cursor = db.cursor()

        cursor.execute("SELECT id, full_name, email FROM customers WHERE phone = %s", (phone,))
        result = cursor.fetchone()
        if result:
            customer_id = result[0]
            update_fields = []
            params = []
            if result[1] != name:
                update_fields.append("full_name = %s")
                params.append(name)
            if email and (len(result) < 3 or result[2] != email):
                update_fields.append("email = %s")
                params.append(email)
            if update_fields:
                params.append(customer_id)
                cursor.execute(f"UPDATE customers SET {', '.join(update_fields)} WHERE id = %s", params)
        else:
            cursor.execute("INSERT INTO customers (full_name, phone, email, visit_count) VALUES (%s, %s, %s, 1)", (name, phone, email))
            customer_id = cursor.lastrowid

        cursor.execute("SELECT plate_number FROM cars WHERE plate_number = %s", (plate,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO cars (plate_number, brand, model, year, customer_id) 
                VALUES (%s, %s, %s, %s, %s)
            """, (plate, brand or None, model or None, year, customer_id))

        cursor.execute("""
            SELECT id FROM appointments 
            WHERE customer_id = %s AND car_plate = %s AND status NOT IN ('Đã bàn giao', 'Hủy lịch')
            ORDER BY appointment_date DESC LIMIT 1
        """, (customer_id, plate))
        existing = cursor.fetchone()

        if existing:
            appt_id = existing[0]
            for sid in selected_services:
                cursor.execute("INSERT IGNORE INTO appointment_services (appointment_id, service_id) VALUES (%s, %s)", (appt_id, sid))
            db.commit()
            messagebox.showinfo("Thành công", f"Đã thêm {len(selected_services)} dịch vụ vào lịch hẹn hiện có!")
        else:
            cursor.execute("""
                INSERT INTO appointments (customer_id, car_plate, appointment_date, status, progress_percent)
                VALUES (%s, %s, %s, 'Chờ xác nhận', 0)
            """, (customer_id, plate, appointment_date))
            appt_id = cursor.lastrowid
            for sid in selected_services:
                cursor.execute("INSERT INTO appointment_services (appointment_id, service_id) VALUES (%s, %s)", (appt_id, sid))
            db.commit()
            messagebox.showinfo("Thành công", f"Đã tạo lịch hẹn mới với {len(selected_services)} dịch vụ!")

        db.close()
        self.modal_window.destroy()
        self.load()


class ServiceDetailsModal(ctk.CTkToplevel):
    """Modal chi tiết dịch vụ: hiển thị vật tư mặc định + đã dùng"""
    def __init__(self, parent, appointment_id, service_id, service_name, service_price):
        super().__init__(parent)
        self.appointment_id = appointment_id
        self.service_id = service_id
        self.service_name = service_name
        self.service_price = service_price
        
        self.title(f"Chi tiết dịch vụ: {service_name}")
        self.geometry("700x600")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="white")
        
        ctk.CTkLabel(self, text=f"CHI TIẾT DỊCH VỤ: {service_name.upper()}", 
                    font=("Arial", 18, "bold"), text_color="#1e293b").pack(pady=20)
        ctk.CTkLabel(self, text=f"Giá dịch vụ: {int(service_price):,} ₫", 
                    font=("Arial", 14), text_color="#10b981").pack(pady=(0, 15))
        
        self.materials_frame = ctk.CTkScrollableFrame(self, fg_color="#f8fafc", corner_radius=10)
        self.materials_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.material_entries = {}
        self.load_service_materials()
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="+ Thêm vật tư khác", fg_color="#10b981", hover_color="#059669",
                     height=40, command=self.add_material).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Lưu thay đổi", fg_color="#3b82f6",
                     height=40, command=self.save_all_materials).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Đóng", fg_color="transparent", text_color="#64748b",
                     height=40, command=self.destroy).pack(side="right", fill="x", expand=True, padx=5)
    
    def load_service_materials(self):
        db = connect_db()
        if not db:
            return
        
        cursor = db.cursor()
        # 1. Lấy vật tư mặc định của service từ bảng service_products
        cursor.execute("""
            SELECT sp.product_id, p.product_name, p.price, p.unit, sp.quantity_needed
            FROM service_products sp
            JOIN inventory p ON sp.product_id = p.id
            WHERE sp.service_id = %s
        """, (self.service_id,))
        default_materials = cursor.fetchall()
        
        # 2. Lấy vật tư đã dùng trong appointment này (của service này)
        cursor.execute("""
            SELECT am.product_id, am.quantity_used
            FROM appointment_materials am
            WHERE am.appointment_id = %s AND am.service_id = %s
        """, (self.appointment_id, self.service_id))
        used_materials = {row[0]: row[1] for row in cursor.fetchall()}
        db.close()
        
        if not default_materials and not used_materials:
            ctk.CTkLabel(self.materials_frame, text="Dịch vụ này không có vật tư nào được khai báo.\nBạn có thể thêm thủ công bên dưới.",
                        font=("Arial", 12), text_color="#64748b").pack(pady=20)
            return
        
        for prod_id, name, price, unit, default_qty in default_materials:
            used_qty = used_materials.get(prod_id, default_qty)
            self.create_material_card(prod_id, name, price, unit, used_qty)
        
        # Vật tư đã dùng nhưng không có trong mặc định (thêm thủ công)
        for prod_id, used_qty in used_materials.items():
            if prod_id not in [m[0] for m in default_materials]:
                db2 = connect_db()
                if db2:
                    cur2 = db2.cursor()
                    cur2.execute("SELECT product_name, price, unit FROM inventory WHERE id = %s", (prod_id,))
                    row = cur2.fetchone()
                    db2.close()
                    if row:
                        self.create_material_card(prod_id, row[0], row[1], row[2], used_qty)
    
    def create_material_card(self, product_id, material_name, price_per_unit, unit, quantity=0):
        card = ctk.CTkFrame(self.materials_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#e2e8f0")
        card.pack(fill="x", pady=8, padx=5)
        
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        ctk.CTkLabel(left, text=material_name, font=("Arial", 14, "bold"), text_color="#1e293b").pack(anchor="w")
        
        qty_frame = ctk.CTkFrame(left, fg_color="transparent")
        qty_frame.pack(anchor="w", pady=(5,0))
        ctk.CTkLabel(qty_frame, text="Số lượng:", font=("Arial", 12)).pack(side="left")
        
        qty_var = ctk.StringVar(value=str(quantity))
        qty_entry = ctk.CTkEntry(qty_frame, textvariable=qty_var, width=80, height=30)
        qty_entry.pack(side="left", padx=(5,0))
        ctk.CTkLabel(qty_frame, text=unit, font=("Arial", 12)).pack(side="left", padx=(5,0))
        
        total_price = quantity * price_per_unit
        price_label = ctk.CTkLabel(left, text=f"Giá: {int(price_per_unit):,} ₫/{unit} = {int(total_price):,} ₫",
                                   font=("Arial", 12), text_color="#10b981")
        price_label.pack(anchor="w")
        
        def update_material_local():
            try:
                new_qty = float(qty_var.get())
                if new_qty < 0:
                    messagebox.showerror("Lỗi", "Số lượng không thể âm!")
                    return
                db = connect_db()
                if db:
                    cursor = db.cursor()
                    if new_qty == 0:
                        cursor.execute("DELETE FROM appointment_materials WHERE appointment_id=%s AND service_id=%s AND product_id=%s",
                                      (self.appointment_id, self.service_id, product_id))
                    else:
                        cursor.execute("""
                            INSERT INTO appointment_materials (appointment_id, service_id, product_id, quantity_used)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE quantity_used = VALUES(quantity_used)
                        """, (self.appointment_id, self.service_id, product_id, new_qty))
                    db.commit()
                    db.close()
                new_total = new_qty * price_per_unit
                price_label.configure(text=f"Giá: {int(price_per_unit):,} ₫/{unit} = {int(new_total):,} ₫")
                messagebox.showinfo("Thành công", f"Đã cập nhật số lượng {material_name}!")
            except ValueError:
                messagebox.showerror("Lỗi", "Số lượng không hợp lệ!")
        
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=15, pady=10)
        ctk.CTkButton(right, text="Cập nhật", width=80, height=30, fg_color="#3b82f6",
                     command=update_material_local).pack(side="left", padx=5)
        
        self.material_entries[product_id] = {
            'var': qty_var,
            'card': card,
            'price': price_per_unit,
            'unit': unit,
            'label_price': price_label
        }
    
    def save_all_materials(self):
        for prod_id, data in self.material_entries.items():
            try:
                new_qty = float(data['var'].get())
                db = connect_db()
                if db:
                    cursor = db.cursor()
                    if new_qty == 0:
                        cursor.execute("DELETE FROM appointment_materials WHERE appointment_id=%s AND service_id=%s AND product_id=%s",
                                      (self.appointment_id, self.service_id, prod_id))
                    else:
                        cursor.execute("""
                            INSERT INTO appointment_materials (appointment_id, service_id, product_id, quantity_used)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE quantity_used = VALUES(quantity_used)
                        """, (self.appointment_id, self.service_id, prod_id, new_qty))
                    db.commit()
                    db.close()
                new_total = new_qty * data['price']
                data['label_price'].configure(text=f"Giá: {int(data['price']):,} ₫/{data['unit']} = {int(new_total):,} ₫")
            except:
                pass
        messagebox.showinfo("Thành công", "Đã lưu tất cả vật tư!")
    
    def add_material(self):
        MaterialSelectionModal(self, self.appointment_id, self.service_id)


class MaterialSelectionModal(ctk.CTkToplevel):
    def __init__(self, parent, appointment_id, service_id):
        super().__init__(parent)
        self.appointment_id = appointment_id
        self.service_id = service_id
        self.title("Chọn vật tư")
        self.geometry("600x500")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="white")
        ctk.CTkLabel(self, text="CHỌN VẬT TƯ", font=("Arial", 18, "bold"), text_color="#1e293b").pack(pady=20)
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0,10))
        ctk.CTkLabel(search_frame, text="🔍", font=("Arial", 14)).pack(side="left")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Tìm vật tư...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(10,0))
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_materials())
        self.materials_frame = ctk.CTkScrollableFrame(self, fg_color="#f8fafc", corner_radius=10)
        self.materials_frame.pack(fill="both", expand=True, padx=20, pady=15)
        self.load_materials()
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Hủy", fg_color="transparent", text_color="#64748b", height=40, command=self.destroy).pack(side="left", fill="x", expand=True, padx=5)
    
    def load_materials(self):
        for w in self.materials_frame.winfo_children():
            w.destroy()
        db = connect_db()
        if not db:
            return
        cursor = db.cursor()
        search = f"%{self.search_entry.get()}%"
        cursor.execute("""
            SELECT id, product_name, price, unit, stock_quantity
            FROM inventory 
            WHERE product_name LIKE %s AND stock_quantity > 0
            ORDER BY product_name
        """, (search,))
        materials = cursor.fetchall()
        db.close()
        if not materials:
            ctk.CTkLabel(self.materials_frame, text="Không tìm thấy vật tư nào!", font=("Arial", 12), text_color="#64748b").pack(pady=20)
            return
        for mat in materials:
            self.create_material_row(*mat)
    
    def create_material_row(self, material_id, name, price, unit, stock):
        row = ctk.CTkFrame(self.materials_frame, fg_color="white", corner_radius=8, border_width=1, border_color="#e2e8f0")
        row.pack(fill="x", pady=5, padx=5)
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        ctk.CTkLabel(info_frame, text=name, font=("Arial", 14, "bold"), text_color="#1e293b").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Giá: {int(price):,} ₫/{unit} | Tồn kho: {stock} {unit}", font=("Arial", 12), text_color="#64748b").pack(anchor="w")
        def select_material():
            qty_dialog = ctk.CTkInputDialog(text=f"Nhập số lượng {name} ({unit}):", title="Số lượng")
            qty_str = qty_dialog.get_input()
            if qty_str:
                try:
                    quantity = float(qty_str)
                    if quantity <= 0:
                        messagebox.showerror("Lỗi", "Số lượng phải lớn hơn 0!")
                        return
                    if quantity > stock:
                        messagebox.showerror("Lỗi", f"Số lượng vượt quá tồn kho ({stock} {unit})!")
                        return
                    db = connect_db()
                    if db:
                        cursor = db.cursor()
                        cursor.execute("""
                            INSERT INTO appointment_materials (appointment_id, service_id, product_id, quantity_used)
                            VALUES (%s, %s, %s, %s)
                        """, (self.appointment_id, self.service_id, material_id, quantity))
                        db.commit()
                        db.close()
                    messagebox.showinfo("Thành công", f"Đã thêm vật tư {name}!")
                    self.destroy()
                except ValueError:
                    messagebox.showerror("Lỗi", "Số lượng không hợp lệ!")
        ctk.CTkButton(row, text="➕ Chọn", width=80, height=35, fg_color="#10b981", command=select_material).pack(side="right", padx=15, pady=10)


class ServiceSelectionModal(ctk.CTkToplevel):
    """Modal chọn dịch vụ để thêm vào lịch hẹn"""
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Chọn dịch vụ")
        self.geometry("600x500")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="white")
        ctk.CTkLabel(self, text="CHỌN DỊCH VỤ", font=("Arial", 18, "bold"), text_color="#1e293b").pack(pady=20)
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0,10))
        ctk.CTkLabel(search_frame, text="🔍", font=("Arial", 14)).pack(side="left")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Tìm dịch vụ...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(10,0))
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_services())
        self.services_frame = ctk.CTkScrollableFrame(self, fg_color="#f8fafc", corner_radius=10)
        self.services_frame.pack(fill="both", expand=True, padx=20, pady=15)
        self.load_services()
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Hủy", fg_color="transparent", text_color="#64748b", height=40, command=self.destroy).pack(side="left", fill="x", expand=True, padx=5)
    
    def load_services(self):
        for w in self.services_frame.winfo_children():
            w.destroy()
        db = connect_db()
        if not db:
            return
        cursor = db.cursor()
        search = f"%{self.search_entry.get()}%"
        cursor.execute("SELECT id, service_name, price, description FROM services WHERE service_name LIKE %s ORDER BY service_name", (search,))
        services = cursor.fetchall()
        db.close()
        if not services:
            ctk.CTkLabel(self.services_frame, text="Không tìm thấy dịch vụ nào!", font=("Arial", 12), text_color="#64748b").pack(pady=20)
            return
        for svc in services:
            self.create_service_row(*svc)
    
    def create_service_row(self, service_id, name, price, description):
        row = ctk.CTkFrame(self.services_frame, fg_color="white", corner_radius=8, border_width=1, border_color="#e2e8f0")
        row.pack(fill="x", pady=5, padx=5)
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        ctk.CTkLabel(info_frame, text=name, font=("Arial", 14, "bold"), text_color="#1e293b").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Giá: {int(price):,} ₫", font=("Arial", 12), text_color="#10b981").pack(anchor="w")
        if description:
            ctk.CTkLabel(info_frame, text=description[:50] + "..." if len(description) > 50 else description, font=("Arial", 11), text_color="#64748b").pack(anchor="w")
        def select_service():
            self.destroy()
            if self.callback:
                self.callback({'id': service_id, 'name': name, 'price': price})
        ctk.CTkButton(row, text="➕ Chọn", width=80, height=35, fg_color="#2563eb", command=select_service).pack(side="right", padx=15, pady=10)