import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from database import connect_db
from datetime import datetime, timedelta
import ctypes

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f1f5f9")
        
        # Sửa lỗi hiển thị DPI trên Windows
        try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except: pass

        self.grid_columnconfigure(0, weight=1)

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, fg_color="white", height=70, corner_radius=0)
        self.header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(self.header, text="Tổng quan hệ thống", font=("Arial", 22, "bold")).pack(side="left", padx=30)
        
        self.filter_var = ctk.StringVar(value="Tất cả")
        self.filter_menu = ctk.CTkComboBox(self.header, values=["Tháng này", "Năm nay", "Tất cả"],
                                          variable=self.filter_var, command=self.update_data)
        self.filter_menu.pack(side="right", padx=30)

        # --- STAT CARDS ---
        self.stat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stat_frame.pack(fill="x", padx=20)
        self.stat_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # --- CHARTS CONTAINER ---
        self.chart_container = ctk.CTkFrame(self, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=20, pady=20)
        self.chart_container.grid_columnconfigure((0, 1), weight=1)

        self.update_data()

    def get_db_stats(self, filter_mode):
        db = connect_db()
        cursor = db.cursor()
        now = datetime.now()
        
        if filter_mode == "Tháng này":
            time_cond = f"MONTH(appointment_date) = {now.month} AND YEAR(appointment_date) = {now.year}"
        elif filter_mode == "Năm nay":
            time_cond = f"YEAR(appointment_date) = {now.year}"
        else:
            time_cond = "1=1"

        # Thống kê số lượng
        cursor.execute("SELECT COUNT(*) FROM customers"); t_cus = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cars"); t_car = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM appointments WHERE {time_cond}"); apps = cursor.fetchone()[0]
        
        # Doanh thu tổng (Fix Decimal lỗi dòng này nếu có)
        cursor.execute(f"SELECT SUM(total_price) FROM appointments WHERE status = 'Hoàn thành' AND {time_cond}")
        rev_val = cursor.fetchone()[0]
        rev = float(rev_val) if rev_val else 0.0
        
        # 2. FIX LỖI TẠI ĐÂY: Dữ liệu biểu đồ doanh thu (6 tháng gần nhất)
        rev_history = []
        for i in range(5, -1, -1):
            # Tính toán tháng lùi lại
            month_date = now.replace(day=1) - timedelta(days=i*30)
            m, y = month_date.month, month_date.year
            
            cursor.execute(f"SELECT SUM(total_price) FROM appointments WHERE status = 'Hoàn thành' AND MONTH(appointment_date) = {m} AND YEAR(appointment_date) = {y}")
            val = cursor.fetchone()[0]
            # Sửa lỗi Decimal / float tại đây
            rev_history.append((f"T{m}", float(val)/1e6 if val else 0.0))

        # 3. Top dịch vụ
        cursor.execute(f"""
            SELECT s.service_name, COUNT(a.id) 
            FROM services s 
            LEFT JOIN appointments a ON s.id = a.service_id AND {time_cond}
            GROUP BY s.id ORDER BY COUNT(a.id) DESC LIMIT 5
        """)
        svc = cursor.fetchall()
        
        db.close()
        return t_cus, t_car, apps, rev, rev_history, svc

    def update_data(self, _=None):
        mode = self.filter_var.get()
        t_cus, t_car, apps, rev, rev_hist, svc_data = self.get_db_stats(mode)
        
        for w in self.stat_frame.winfo_children(): w.destroy()
        rev_display = f"{rev/1e6:.1f}tr" if rev >= 1e6 else f"{rev:,.0f}đ"

        stats = [
            ("Tổng khách hàng", t_cus, "+12%", "#22c55e"),
            ("Xe đang quản lý", t_car, "+8%", "#22c55e"),
            ("Lịch hẹn", apps, "-3%", "#ef4444"),
            ("Doanh thu", rev_display, "+15%", "#22c55e")
        ]

        for i, (title, val, sub, color) in enumerate(stats):
            card = ctk.CTkFrame(self.stat_frame, fg_color="white", corner_radius=15)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=("Arial", 13), text_color="#64748b").pack(pady=(15, 0))
            ctk.CTkLabel(card, text=str(val), font=("Arial", 24, "bold")).pack(pady=5)
            ctk.CTkLabel(card, text=sub, font=("Arial", 11), text_color=color).pack(pady=(0,15))

        self.render_all_charts(rev_hist, svc_data)

    def render_all_charts(self, rev_hist, svc_data):
        for w in self.chart_container.winfo_children(): w.destroy()

        # BIỂU ĐỒ DOANH THU
        fig1, ax1 = plt.subplots(figsize=(5, 4), facecolor='white')
        months = [x[0] for x in rev_hist]
        values = [x[1] for x in rev_hist]
        ax1.plot(months, values, marker='o', color='#3b82f6', linewidth=2)
        ax1.fill_between(months, values, color='#3b82f6', alpha=0.1)
        ax1.set_title("Biến động doanh thu (Tr)", fontsize=11, fontweight='bold')
        ax1.spines[['top', 'right']].set_visible(False)

        canvas1 = FigureCanvasTkAgg(fig1, self.chart_container)
        canvas1.get_tk_widget().grid(row=0, column=0, padx=10, sticky="nsew")

        # BIỂU ĐỒ DỊCH VỤ
        fig2, ax2 = plt.subplots(figsize=(5, 4), facecolor='white')
        svc_names = [s[0][:10] for s in svc_data]
        svc_counts = [s[1] for s in svc_data]
        ax2.bar(svc_names, svc_counts, color='#6366f1', width=0.5)
        ax2.set_title("Dịch vụ phổ biến", fontsize=11, fontweight='bold')
        ax2.spines[['top', 'right']].set_visible(False)

        canvas2 = FigureCanvasTkAgg(fig2, self.chart_container)
        canvas2.get_tk_widget().grid(row=0, column=1, padx=10, sticky="nsew")
        
        plt.tight_layout()