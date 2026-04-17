import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from database import connect_db
from datetime import datetime, timedelta
import ctypes

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f1f5f9")
        
        # Tối ưu hiển thị trên màn hình độ phân giải cao
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

        # --- STAT CARDS (Thống kê nhanh) ---
        self.stat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stat_frame.pack(fill="x", padx=20)
        self.stat_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # --- CHARTS CONTAINER (Cuộn được nếu màn hình nhỏ) ---
        self.chart_container = ctk.CTkScrollableFrame(self, fg_color="transparent", height=800)
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
        
        cursor.execute(f"SELECT SUM(total_price) FROM appointments WHERE status = 'Hoàn thành' AND {time_cond}")
        rev_val = cursor.fetchone()[0]
        rev = float(rev_val) if rev_val else 0.0
        
        # Doanh thu 6 tháng gần nhất
        rev_history = []
        for i in range(5, -1, -1):
            month_date = now.replace(day=1) - timedelta(days=i*30)
            m, y = month_date.month, month_date.year
            cursor.execute(f"SELECT SUM(total_price) FROM appointments WHERE status = 'Hoàn thành' AND MONTH(appointment_date) = {m} AND YEAR(appointment_date) = {y}")
            val = cursor.fetchone()[0]
            rev_history.append((f"T{m}", float(val)/1e6 if val else 0.0))

        # 1. FIX: Top 5 khách hàng (Sử dụng LEFT JOIN để luôn lấy đủ 5 người kể cả khi mới)
        cursor.execute(f"""
            SELECT c.full_name, COALESCE(SUM(a.total_price), 0) as total
            FROM customers c
            LEFT JOIN appointments a ON c.id = a.customer_id AND a.status = 'Hoàn thành'
            GROUP BY c.id, c.full_name
            ORDER BY total DESC, c.full_name ASC
            LIMIT 5
        """)
        top_customers = cursor.fetchall()

        # 2. FIX: Top 5 dịch vụ phổ biến (Sử dụng LEFT JOIN để không bị thiếu mục)
        cursor.execute(f"""
            SELECT s.service_name, COUNT(a.id) as usage_count
            FROM services s
            LEFT JOIN appointments a ON s.id = a.service_id
            GROUP BY s.id, s.service_name
            ORDER BY usage_count DESC, s.service_name ASC
            LIMIT 5
        """)
        svc_data = cursor.fetchall()
        
        db.close()
        return t_cus, t_car, apps, rev, rev_history, svc_data, top_customers

    def format_label(self, text, max_len=12):
        """Hàm tự động chèn dấu xuống dòng để chữ nằm ngang không bị đè nhau"""
        if len(text) <= max_len:
            return text
        words = text.split()
        if len(words) > 1:
            mid = len(words) // 2
            return " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
        return text

    def update_data(self, _=None):
        mode = self.filter_var.get()
        t_cus, t_car, apps, rev, rev_hist, svc_data, top_cust = self.get_db_stats(mode)
        
        for w in self.stat_frame.winfo_children(): w.destroy()
        rev_display = f"{rev/1e6:.1f}tr" if rev >= 1e6 else f"{rev:,.0f}đ"

        stats = [
            ("Tổng khách hàng", t_cus, "Hệ thống", "#22c55e"),
            ("Xe đang quản lý", t_car, "Hệ thống", "#22c55e"),
            ("Lịch hẹn", apps, mode, "#3b82f6"),
            ("Doanh thu", rev_display, mode, "#22c55e")
        ]

        for i, (title, val, sub, color) in enumerate(stats):
            card = ctk.CTkFrame(self.stat_frame, fg_color="white", corner_radius=15)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=("Arial", 13), text_color="#64748b").pack(pady=(15, 0))
            ctk.CTkLabel(card, text=str(val), font=("Arial", 24, "bold")).pack(pady=5)
            ctk.CTkLabel(card, text=sub, font=("Arial", 11), text_color=color).pack(pady=(0,15))

        self.render_all_charts(rev_hist, svc_data, top_cust)

    def render_all_charts(self, rev_hist, svc_data, top_cust):
        for w in self.chart_container.winfo_children(): w.destroy()

        # --- BIỂU ĐỒ DOANH THU ---
        fig1, ax1 = plt.subplots(figsize=(5, 3.5), facecolor='white')
        months = [x[0] for x in rev_hist]
        values = [x[1] for x in rev_hist]
        ax1.plot(months, values, marker='o', color='#3b82f6', linewidth=2)
        ax1.set_title("Biến động doanh thu (Tr)", fontsize=10, fontweight='bold')
        ax1.spines[['top', 'right']].set_visible(False)
        FigureCanvasTkAgg(fig1, self.chart_container).get_tk_widget().grid(row=0, column=0, padx=10, pady=10)

        # --- BIỂU ĐỒ TOP 5 KHÁCH HÀNG ---
        fig2, ax2 = plt.subplots(figsize=(5, 3.5), facecolor='white')
        if top_cust:
            cust_names = [self.format_label(c[0], 12) for c in top_cust]
            cust_revs = [float(c[1])/1e6 for c in top_cust]
            ax2.barh(cust_names, cust_revs, color='#10b981')
            ax2.invert_yaxis()
        ax2.set_title("Top khách hàng chi tiêu (Tr)", fontsize=10, fontweight='bold')
        ax2.spines[['top', 'right']].set_visible(False)
        FigureCanvasTkAgg(fig2, self.chart_container).get_tk_widget().grid(row=0, column=1, padx=10, pady=10)

        # --- BIỂU ĐỒ TOP 5 DỊCH VỤ (Rộng ngang màn hình) ---
        fig3, ax3 = plt.subplots(figsize=(10, 4.5), facecolor='white')
        if svc_data:
            svc_names = [self.format_label(s[0], 10) for s in svc_data]
            svc_counts = [s[1] for s in svc_data]
            bars = ax3.bar(svc_names, svc_counts, color='#6366f1', width=0.4)
            
            # Label số lượng trên cột
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height, 
                        f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        ax3.set_title("Top 5 dịch vụ phổ biến (Lượt dùng)", fontsize=11, fontweight='bold')
        ax3.set_ylim(0, max([s[1] for s in svc_data] + [1]) * 1.3) # Tạo khoảng trống cho số hiện trên đầu cột
        ax3.spines[['top', 'right']].set_visible(False)
        
        plt.tight_layout()
        FigureCanvasTkAgg(fig3, self.chart_container).get_tk_widget().grid(row=1, column=0, columnspan=2, pady=20)