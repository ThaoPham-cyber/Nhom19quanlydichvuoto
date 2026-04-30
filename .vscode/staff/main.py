import customtkinter as ctk
from tkinter import messagebox
from database import connect_db
import threading
import time
from datetime import datetime

# Import các module
from gui_customers import CustomerFrame
from gui_cars import CarFrame 
from gui_services import ServiceFrame 
from gui_inventory import InventoryFrame 
from gui_appointments import AppointmentFrame
from gui_payments import PaymentFrame
import os

class QuickPaymentWindow(ctk.CTkToplevel):
    """Cửa sổ thanh toán nhanh"""
    def __init__(self, parent, appointment_id=None, customer_name="", car_plate="", service_name="", amount=0):
        super().__init__(parent)
        self.parent = parent
        self.appointment_id = appointment_id
        self.title("Thanh toán nhanh")
        self.geometry("500x600")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="white")
        
        # Header
        ctk.CTkLabel(self, text="THANH TOÁN NHANH", 
                    font=("Arial", 20, "bold"), text_color="#1e293b").pack(pady=20)
        
        # Form frame
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        # Thông tin
        info_frame = ctk.CTkFrame(form_frame, fg_color="#f8fafc", corner_radius=12)
        info_frame.pack(fill="x", pady=10)
        
        info_items = [
            ("Mã lịch hẹn:", f"AP{appointment_id:04d}" if appointment_id else "---"),
            ("Khách hàng:", customer_name),
            ("Biển số:", car_plate),
            ("Dịch vụ:", service_name),
            ("Số tiền:", f"{int(amount):,} đ" if amount else "0 đ")
        ]
        
        for label, value in info_items:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(row, text=label, font=("Arial", 12), width=120, 
                        text_color="#64748b").pack(side="left")
            value_color = "#ef4444" if label == "Số tiền:" else "#1e293b"
            font_bold = ("Arial", 14, "bold") if label == "Số tiền:" else ("Arial", 13)
            ctk.CTkLabel(row, text=value, font=font_bold, 
                        text_color=value_color).pack(side="left", padx=10)
        
        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#e2e8f0").pack(fill="x", padx=40, pady=15)
        
        # Số tiền thanh toán
        amount_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        amount_frame.pack(fill="x", pady=15)
        
        ctk.CTkLabel(amount_frame, text="Số tiền thanh toán *", 
                    font=("Arial", 13, "bold")).pack(anchor="w")
        self.payment_amount = ctk.CTkEntry(amount_frame, height=45, font=("Arial", 14))
        self.payment_amount.pack(fill="x", pady=(5, 0))
        self.payment_amount.insert(0, str(int(amount)) if amount else "0")
        
        # Phương thức thanh toán
        method_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        method_frame.pack(fill="x", pady=15)
        
        ctk.CTkLabel(method_frame, text="Phương thức thanh toán *", 
                    font=("Arial", 13, "bold")).pack(anchor="w")
        self.payment_method = ctk.CTkComboBox(method_frame, 
                                             values=["Tiền mặt", "Chuyển khoản", "Momo", "ZaloPay"],
                                             height=40)
        self.payment_method.pack(fill="x", pady=(5, 0))
        self.payment_method.set("Tiền mặt")
        
        # Ghi chú
        note_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        note_frame.pack(fill="x", pady=15)
        
        ctk.CTkLabel(note_frame, text="Ghi chú", font=("Arial", 13, "bold")).pack(anchor="w")
        self.note_entry = ctk.CTkEntry(note_frame, height=40, placeholder_text="Nhập ghi chú (nếu có)")
        self.note_entry.pack(fill="x", pady=(5, 0))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkButton(btn_frame, text="Hủy", fg_color="transparent", 
                     text_color="#64748b", height=45, command=self.destroy).pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(btn_frame, text="Xác nhận thanh toán", fg_color="#10b981", 
                     height=45, command=self.process_payment).pack(side="right", fill="x", expand=True, padx=5)
    
    def process_payment(self):
        """Xử lý thanh toán"""
        amount_str = self.payment_amount.get().strip().replace(",", "")
        
        try:
            amount = int(float(amount_str))
        except:
            messagebox.showerror("Lỗi", "Vui lòng nhập số tiền hợp lệ!")
            return
        
        if amount <= 0:
            messagebox.showerror("Lỗi", "Số tiền thanh toán phải lớn hơn 0!")
            return
        
        payment_method = self.payment_method.get()
        note = self.note_entry.get()
        
        db = connect_db()
        if not db:
            return
        
        cursor = db.cursor()
        try:
            if self.appointment_id:
                # Lấy thông tin appointment
                cursor.execute("""
                    SELECT a.customer_id, a.car_plate, a.appointment_date, s.price, s.service_name, s.id
                    FROM appointments a
                    LEFT JOIN services s ON a.service_id = s.id
                    WHERE a.id = %s
                """, (self.appointment_id,))
                appt_data = cursor.fetchone()
                
                if appt_data:
                    # Tạo invoice
                    cursor.execute("""
                        INSERT INTO invoices (appointment_id, customer_id, total_amount, status, created_at)
                        VALUES (%s, %s, %s, 'Đã thanh toán', NOW())
                    """, (self.appointment_id, appt_data[0], appt_data[3]))
                    invoice_id = cursor.lastrowid
                    
                    # Thêm invoice item
                    cursor.execute("""
                        INSERT INTO invoice_items (invoice_id, service_id, service_name, price, quantity)
                        VALUES (%s, %s, %s, %s, 1)
                    """, (invoice_id, appt_data[5], appt_data[4], appt_data[3]))
                    
                    # Thêm payment
                    cursor.execute("""
                        INSERT INTO payments (invoice_id, amount, payment_method, payment_date, note)
                        VALUES (%s, %s, %s, NOW(), %s)
                    """, (invoice_id, amount, payment_method, note))
                    
                    # Xóa appointment
                    cursor.execute("DELETE FROM appointments WHERE id = %s", (self.appointment_id,))
                    
                    db.commit()
                    messagebox.showinfo("Thành công", f"Đã thanh toán {amount:,} đ thành công!")
                    
                    # Refresh các trang
                    if hasattr(self.parent, 'refresh_all_data'):
                        self.parent.refresh_all_data()
                    if hasattr(self.parent, 'refresh_appointments'):
                        self.parent.refresh_appointments()
                    if hasattr(self.parent, 'refresh_payments'):
                        self.parent.refresh_payments()
                    
                    self.destroy()
            else:
                messagebox.showerror("Lỗi", "Không tìm thấy thông tin lịch hẹn!")
                
        except Exception as e:
            db.rollback()
            messagebox.showerror("Lỗi", f"Không thể xử lý thanh toán: {e}")
        finally:
            db.close()


class DashboardFrame(ctk.CTkFrame):
    """Dashboard - Trang tổng quan với real-time data"""
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        self.parent_app = parent
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # Auto-refresh settings
        self.refresh_running = True
        self.refresh_interval = 5000  # 5 giây
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=20)
        
        ctk.CTkLabel(header, text="📊 Tổng quan", font=("Arial", 28, "bold"), 
                    text_color="#1e293b").pack(side="left")
        
        ctk.CTkLabel(header, text="Xin chào Admin!", font=("Arial", 14), 
                    text_color="#64748b").pack(side="left", padx=20)
        
        # Refresh controls
        control_frame = ctk.CTkFrame(header, fg_color="transparent")
        control_frame.pack(side="right")
        
        self.refresh_btn = ctk.CTkButton(
            control_frame, text="🔄 Làm mới", width=100, height=35,
            fg_color="#3b82f6", hover_color="#2563eb",
            command=self.refresh_all_data
        )
        self.refresh_btn.pack(side="left", padx=5)
        
        self.auto_refresh_var = ctk.BooleanVar(value=True)
        self.auto_refresh_btn = ctk.CTkSwitch(
            control_frame, text="Tự động", variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh, button_color="#3b82f6"
        )
        self.auto_refresh_btn.pack(side="left", padx=5)
        
        self.last_update_label = ctk.CTkLabel(
            control_frame, text="", font=("Arial", 10), text_color="#64748b"
        )
        self.last_update_label.pack(side="left", padx=10)
        
        # Statistics cards
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=20)
        
        for i in range(4):
            self.stats_frame.grid_columnconfigure(i, weight=1)
        
        self.stat_cards = {}
        stats_titles = [
            ("Tổng khách hàng", "👥", "#3b82f6"),
            ("Tổng xe", "🚗", "#10b981"),
            ("Chờ xác nhận", "⏳", "#f59e0b"),
            ("Doanh thu tháng", "💰", "#ef4444")
        ]
        
        for i, (title, icon, color) in enumerate(stats_titles):
            card = ctk.CTkFrame(self.stats_frame, fg_color="white", corner_radius=12, height=120)
            card.grid(row=0, column=i, sticky="nsew", padx=5)
            
            ctk.CTkLabel(card, text=icon, font=("Arial", 32)).pack(anchor="w", padx=15, pady=(15, 0))
            ctk.CTkLabel(card, text=title, font=("Arial", 12), text_color="#64748b").pack(anchor="w", padx=15)
            
            value_label = ctk.CTkLabel(card, text="0", font=("Arial", 20, "bold"), text_color=color)
            value_label.pack(anchor="w", padx=15, pady=(5, 15))
            
            self.stat_cards[title] = value_label
        
        # Pending appointments section
        pending_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15,
                                     border_width=1, border_color="#e2e8f0")
        pending_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 20))
        
        pending_header = ctk.CTkFrame(pending_frame, fg_color="transparent")
        pending_header.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(pending_header, text="⏳ LỊCH HẸN CHỜ XÁC NHẬN", 
                    font=("Arial", 16, "bold"), text_color="#f59e0b").pack(side="left")
        
        btn_frame = ctk.CTkFrame(pending_header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="Xem tất cả", width=100, height=30,
                     fg_color="transparent", text_color="#3b82f6",
                     command=self.view_all_appointments).pack(side="right")
        
        self.pending_list = ctk.CTkScrollableFrame(pending_frame, fg_color="transparent",
                                                   height=250)
        self.pending_list.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Recent activities section
        recent_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15,
                                    border_width=1, border_color="#e2e8f0")
        recent_frame.grid(row=3, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        ctk.CTkLabel(recent_frame, text="📋 HOẠT ĐỘNG GẦN ĐÂY", 
                    font=("Arial", 16, "bold"), text_color="#2563eb").pack(anchor="w", padx=20, pady=(15, 10))
        
        self.recent_list = ctk.CTkScrollableFrame(recent_frame, fg_color="transparent")
        self.recent_list.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Start auto-refresh
        self.start_auto_refresh()
        
        # Initial load
        self.refresh_all_data()
    
    def start_auto_refresh(self):
        """Start auto-refresh thread"""
        def refresh_loop():
            while self.refresh_running:
                if self.auto_refresh_var.get():
                    self.after(0, self.refresh_all_data)
                time.sleep(self.refresh_interval / 1000)
        
        thread = threading.Thread(target=refresh_loop, daemon=True)
        thread.start()
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        if self.auto_refresh_var.get():
            self.refresh_btn.configure(text="🔄 Đang tự động...", fg_color="#10b981")
        else:
            self.refresh_btn.configure(text="🔄 Làm mới", fg_color="#3b82f6")
    
    def refresh_all_data(self):
        """Refresh all dashboard data"""
        self.load_statistics()
        self.load_pending_appointments()
        self.load_recent_activities()
        
        # Update last update time
        self.last_update_label.configure(text=f"📍 {datetime.now().strftime('%H:%M:%S')}")
    
    def load_statistics(self):
        """Load statistics from database"""
        db = connect_db()
        if not db:
            return
        
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM customers")
            total_customers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cars")
            total_cars = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Chờ xác nhận'")
            pending_appointments = cursor.fetchone()[0]
            
            current_month = datetime.now().month
            current_year = datetime.now().year
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                WHERE MONTH(payment_date) = %s AND YEAR(payment_date) = %s
            """, (current_month, current_year))
            monthly_revenue = cursor.fetchone()[0]
            
            self.stat_cards["Tổng khách hàng"].configure(text=f"{total_customers:,}")
            self.stat_cards["Tổng xe"].configure(text=f"{total_cars:,}")
            
            pending_color = "#ef4444" if pending_appointments > 0 else "#10b981"
            self.stat_cards["Chờ xác nhận"].configure(text=f"{pending_appointments:,}", text_color=pending_color)
            self.stat_cards["Doanh thu tháng"].configure(text=f"{int(monthly_revenue):,} ₫")
                
        except Exception as e:
            print(f"Lỗi load statistics: {e}")
        
        db.close()
    
    def load_pending_appointments(self):
        """Load pending appointments"""
        for w in self.pending_list.winfo_children():
            w.destroy()
        
        db = connect_db()
        if not db:
            return
        
        cursor = db.cursor()
        try:
            cursor.execute("""
                SELECT a.id, c.full_name, a.car_plate, 
                       COALESCE(s.service_name, 'Không rõ') as service_name,
                       a.appointment_date, s.price
                FROM appointments a
                JOIN customers c ON a.customer_id = c.id
                LEFT JOIN services s ON a.service_id = s.id
                WHERE a.status = 'Chờ xác nhận'
                ORDER BY a.appointment_date ASC
                LIMIT 10
            """)
            
            appointments = cursor.fetchall()
            
            if appointments:
                for appt in appointments:
                    self.create_pending_card(appt)
            else:
                empty_label = ctk.CTkLabel(
                    self.pending_list, 
                    text="✅ Không có lịch hẹn chờ xác nhận",
                    font=("Arial", 14), text_color="#10b981"
                )
                empty_label.pack(pady=30)
                
        except Exception as e:
            ctk.CTkLabel(self.pending_list, text=f"Lỗi: {e}", 
                        text_color="#ef4444").pack(pady=20)
        
        db.close()
    
    def create_pending_card(self, appt):
        """Create card for pending appointment"""
        card = ctk.CTkFrame(self.pending_list, fg_color="#fef3c7", corner_radius=10,
                           border_width=1, border_color="#fde68a")
        card.pack(fill="x", pady=5, padx=5)
        
        left_frame = ctk.CTkFrame(card, fg_color="transparent")
        left_frame.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(left_frame, text=appt[1], font=("Arial", 14, "bold"),
                    text_color="#92400e").pack(anchor="w")
        
        ctk.CTkLabel(left_frame, text=f"🚗 {appt[2]}  •  🔧 {appt[3]}", 
                    font=("Arial", 11), text_color="#b45309").pack(anchor="w")
        
        if appt[4]:
            date_str = appt[4].strftime("%d/%m/%Y - %H:%M")
            ctk.CTkLabel(left_frame, text=f"📅 {date_str}", 
                        font=("Arial", 11), text_color="#b45309").pack(anchor="w")
        
        if appt[5]:
            ctk.CTkLabel(left_frame, text=f"💰 {int(appt[5]):,} đ", 
                        font=("Arial", 11), text_color="#10b981").pack(anchor="w")
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=15, pady=10)
        
        ctk.CTkButton(btn_frame, text="✓ Xác nhận", width=100, height=32,
                     fg_color="#10b981", hover_color="#059669",
                     command=lambda: self.confirm_appointment(appt[0])).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="💰 Thanh toán", width=100, height=32,
                     fg_color="#3b82f6", hover_color="#2563eb",
                     command=lambda: self.quick_payment(appt[0], appt[1], appt[2], appt[3], appt[5])).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="✗ Hủy", width=80, height=32,
                     fg_color="#ef4444", hover_color="#dc2626",
                     command=lambda: self.cancel_appointment(appt[0])).pack(side="left")
    
    def quick_payment(self, appointment_id, customer_name, car_plate, service_name, amount):
        """Mở cửa sổ thanh toán nhanh"""
        QuickPaymentWindow(self, appointment_id, customer_name, car_plate, service_name, amount)
    
    def confirm_appointment(self, appointment_id):
        """Confirm appointment"""
        if messagebox.askyesno("Xác nhận", "Xác nhận lịch hẹn này?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                try:
                    cursor.execute("""
                        UPDATE appointments 
                        SET status = 'Đã xác nhận' 
                        WHERE id = %s
                    """, (appointment_id,))
                    db.commit()
                    
                    messagebox.showinfo("Thành công", "Đã xác nhận lịch hẹn!")
                    self.refresh_all_data()
                    
                    if hasattr(self.parent_app, 'refresh_appointments'):
                        self.parent_app.refresh_appointments()
                        
                except Exception as e:
                    db.rollback()
                    messagebox.showerror("Lỗi", str(e))
                finally:
                    db.close()
    
    def cancel_appointment(self, appointment_id):
        """Cancel appointment"""
        if messagebox.askyesno("Xác nhận", "Hủy lịch hẹn này?"):
            db = connect_db()
            if db:
                cursor = db.cursor()
                try:
                    cursor.execute("""
                        UPDATE appointments 
                        SET status = 'Hủy lịch' 
                        WHERE id = %s
                    """, (appointment_id,))
                    db.commit()
                    
                    messagebox.showinfo("Thành công", "Đã hủy lịch hẹn!")
                    self.refresh_all_data()
                    
                    if hasattr(self.parent_app, 'refresh_appointments'):
                        self.parent_app.refresh_appointments()
                        
                except Exception as e:
                    db.rollback()
                    messagebox.showerror("Lỗi", str(e))
                finally:
                    db.close()
    
    def view_all_appointments(self):
        """Switch to appointments page"""
        if hasattr(self.parent_app, 'show_frame'):
            self.parent_app.show_frame("AppointmentFrame")
    
    def load_recent_activities(self):
        """Load recent activities"""
        for w in self.recent_list.winfo_children():
            w.destroy()
        
        db = connect_db()
        if not db:
            return
        
        cursor = db.cursor()
        try:
            cursor.execute("""
                SELECT a.id, c.full_name, a.car_plate, a.appointment_date, a.status
                FROM appointments a
                JOIN customers c ON a.customer_id = c.id
                WHERE a.status != 'Hủy lịch'
                ORDER BY a.appointment_date DESC
                LIMIT 15
            """)
            
            appointments = cursor.fetchall()
            
            if appointments:
                for appt in appointments:
                    self.create_activity_item(appt)
            else:
                ctk.CTkLabel(self.recent_list, text="Chưa có hoạt động nào", 
                            text_color="#94a3b8").pack(pady=30)
        except Exception as e:
            ctk.CTkLabel(self.recent_list, text=f"Lỗi: {e}", 
                        text_color="#ef4444").pack(pady=20)
        
        db.close()
    
    def create_activity_item(self, appt):
        """Create activity item"""
        item = ctk.CTkFrame(self.recent_list, fg_color="#f8fafc", corner_radius=8)
        item.pack(fill="x", pady=3)
        
        left = ctk.CTkFrame(item, fg_color="transparent")
        left.pack(side="left", padx=15, pady=10, fill="both", expand=True)
        
        status_icons = {
            "Đã xác nhận": "✅",
            "Đã hoàn thành": "✔️",
            "Đã bàn giao": "🎉",
            "Chờ xác nhận": "⏳"
        }
        icon = status_icons.get(appt[4], "📋")
        
        ctk.CTkLabel(left, text=f"{icon} {appt[1]}", font=("Arial", 13, "bold")).pack(anchor="w")
        
        date_str = appt[3].strftime('%d/%m/%Y %H:%M') if appt[3] else ''
        ctk.CTkLabel(left, text=f"🚗 {appt[2]} • {date_str}", 
                    font=("Arial", 11), text_color="#64748b").pack(anchor="w")
        
        status_color = {
            "Chờ xác nhận": "#facc15", 
            "Đã xác nhận": "#60a5fa", 
            "Đã hoàn thành": "#22c55e", 
            "Đã bàn giao": "#10b981"
        }.get(appt[4], "#e5e7eb")
        
        right = ctk.CTkFrame(item, fg_color="transparent")
        right.pack(side="right", padx=15, pady=10)
        
        ctk.CTkLabel(right, text=appt[4], fg_color=status_color, 
                    corner_radius=6, padx=10).pack()


class AutoCareApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AutoCare Manager - Admin Dashboard")
        self.geometry("1200x750")
        self.configure(fg_color="#f8fafc")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#0f172a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=30)
        
        ctk.CTkLabel(logo_frame, text="🚗 AUTOCARE", font=("Arial", 22, "bold"),
                    text_color="#3b82f6").pack()
        ctk.CTkLabel(logo_frame, text="Hệ thống quản lý garage",
                    font=("Arial", 11), text_color="#64748b").pack()

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#1e293b").pack(fill="x", padx=20, pady=10)

        # Navigation
        nav_items = [
            ("📊 Tổng quan", "DashboardFrame"),
            ("📅 Lịch hẹn", "AppointmentFrame"),
            ("👥 Khách hàng", "CustomerFrame"),
            ("🚗 Xe", "CarFrame"),
            ("🔧 Dịch vụ", "ServiceFrame"),
            ("📦 Kho hàng", "InventoryFrame"),
            ("💰 Thanh toán", "PaymentFrame")
        ]

        for text, page_name in nav_items:
            self.create_nav_button(text, page_name)

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#1e293b").pack(fill="x", padx=20, pady=10)

        # Admin info
        admin_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        admin_frame.pack(side="bottom", pady=20, fill="x", padx=15)
        ctk.CTkLabel(admin_frame, text="👨‍💼 Admin", font=("Arial", 12, "bold"),
                    text_color="#e2e8f0").pack()
        ctk.CTkLabel(admin_frame, text="Quản lý hệ thống", font=("Arial", 10),
                    text_color="#64748b").pack()

        # Container
        self.container = ctk.CTkFrame(self, fg_color="#f8fafc", corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.appointment_frame = None
        self.payment_frame = None

        # Pages
        pages = {
            "DashboardFrame": DashboardFrame,
            "CustomerFrame": CustomerFrame,
            "CarFrame": CarFrame,
            "ServiceFrame": ServiceFrame,
            "InventoryFrame": InventoryFrame,
            "AppointmentFrame": AppointmentFrame,
            "PaymentFrame": PaymentFrame
        }

        # Create frames
        for page_name, FrameClass in pages.items():
            try:
                frame = FrameClass(self.container)
                self.frames[page_name] = frame
                frame.grid(row=0, column=0, sticky="nsew")
                
                if page_name == "AppointmentFrame":
                    self.appointment_frame = frame
                if page_name == "PaymentFrame":
                    self.payment_frame = frame
                    
            except Exception as e:
                print(f"Lỗi khi tạo {page_name}: {e}")
                temp_frame = ctk.CTkFrame(self.container, fg_color="#f8fafc")
                temp_frame.grid(row=0, column=0, sticky="nsew")
                ctk.CTkLabel(temp_frame, text=f"⚠️ Lỗi: Không thể tải {page_name}\n{str(e)}", 
                            wraplength=400, text_color="#ef4444").pack(expand=True)
                self.frames[page_name] = temp_frame

        self.show_frame("DashboardFrame")

    def create_nav_button(self, text, page_name):
        btn = ctk.CTkButton(
            self.sidebar, text=text, height=45, fg_color="transparent",
            text_color="#e2e8f0", hover_color="#1e293b", anchor="w",
            font=("Arial", 13), corner_radius=8,
            command=lambda: self.show_frame(page_name)
        )
        btn.pack(pady=4, padx=15, fill="x")

    def refresh_appointments(self):
        """Refresh appointments page if exists"""
        if self.appointment_frame and hasattr(self.appointment_frame, 'load'):
            self.appointment_frame.load()
    
    def refresh_payments(self):
        """Refresh payments page if exists"""
        if self.payment_frame and hasattr(self.payment_frame, 'load_invoices'):
            self.payment_frame.load_invoices()
    
    def refresh_dashboard(self):
        """Refresh dashboard page if exists"""
        if "DashboardFrame" in self.frames:
            dashboard = self.frames["DashboardFrame"]
            if hasattr(dashboard, 'refresh_all_data'):
                dashboard.refresh_all_data()
    
    def show_payment_tab(self):
        """Chuyển sang tab thanh toán"""
        # Chuyển đến PaymentFrame
        self.show_frame("PaymentFrame")
        
        # Refresh dữ liệu thanh toán nếu cần
        if self.payment_frame and hasattr(self.payment_frame, 'load_invoices'):
            self.payment_frame.load_invoices()
        
        # Nếu có sử dụng CTkTabview, có thể dùng dòng này
        # if hasattr(self, 'tabview'):
        #     self.tabview.set("Thanh toán")

    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]
            frame.tkraise()
            
            # Auto reload data
            if hasattr(frame, "load"):
                frame.load()
            elif hasattr(frame, "load_data"):
                frame.load_data()
            elif hasattr(frame, "load_services"):
                frame.load_services()
            elif hasattr(frame, "load_inventory"):
                frame.load_inventory()
            elif hasattr(frame, "load_invoices"):
                frame.load_invoices()
                
            # Refresh dashboard if coming back
            if page_name == "DashboardFrame" and hasattr(frame, 'refresh_all_data'):
                frame.refresh_all_data()
        else:
            messagebox.showerror("Lỗi", f"Không tìm thấy trang {page_name}")
            


if __name__ == "__main__":
    app = AutoCareApp()
    app.mainloop()