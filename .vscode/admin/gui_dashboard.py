import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from database import connect_db
from datetime import datetime, timedelta

def to_float(v):
    return float(v) if v else 0.0

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, app=None):
        super().__init__(parent, fg_color="#f1f5f9") # Nền xám nhạt sang trọng
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ===== HEADER =====
        header = ctk.CTkFrame(self, fg_color="white", height=70, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            header,
            text="Hệ Thống Dashboard Realtime",
            font=("Arial", 22, "bold"),
            text_color="#1e293b"
        ).pack(side="left", padx=30)

        self.filter_var = ctk.StringVar(value="Năm")
        self.sync_btn = ctk.CTkButton(
            header,
            text="🔄 Đồng bộ",
            width=120,
            fg_color="#10b981",
            hover_color="#059669",
            command=self.update_data
        )
        self.sync_btn.pack(side="right", padx=10)
        ctk.CTkComboBox(
            header,
            values=["Ngày", "Tuần", "Tháng", "Năm"],
            variable=self.filter_var,
            command=self.update_data,
            width=140,
            border_color="#e2e8f0",
            button_color="#2563eb"
        ).pack(side="right", padx=20)

        # ===== SCROLLABLE AREA =====
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll.grid_columnconfigure(0, weight=1)

        # Khu vực Stats (4 ô trên cùng)
        self.stat_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.stat_frame.pack(fill="x", pady=(10, 20))
        self.stat_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Khu vực Biểu đồ
        self.chart_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.chart_frame.pack(fill="both", expand=True)
        self.chart_frame.grid_columnconfigure((0, 1), weight=1)
        self.chart_frame.grid_rowconfigure((0, 1), weight=1)

        self.revenue_highlight_card = None

        # ===== START =====
        self.update_data()
        self.auto_refresh()


    def get_data(self):
        db = connect_db()
        cursor = db.cursor()
        now = datetime.now()
        mode = self.filter_var.get()

        if mode == "Ngày":
            cond = "DATE(p.payment_date) = %s"
            params = (now.date(),)
        elif mode == "Tuần":
            cond = "YEARWEEK(p.payment_date, 1) = YEARWEEK(NOW(), 1)"
            params = ()
        elif mode == "Tháng":
            cond = "MONTH(p.payment_date) = %s AND YEAR(p.payment_date) = %s"
            params = (now.month, now.year)
        else:
            cond = "YEAR(p.payment_date) = %s"
            params = (now.year,)

        # Queries
        cursor.execute("SELECT COUNT(*) FROM customers")
        cus = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cars")
        cars = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM appointments")
        apps = cursor.fetchone()[0]

        cursor.execute(f"SELECT SUM(p.amount) FROM payments p WHERE {cond}", params)
        rev = to_float(cursor.fetchone()[0])

        # Revenue Line Chart (7 days)
        revenue = []
        for i in range(6, -1, -1):
            d = now - timedelta(days=i)
            cursor.execute("SELECT SUM(amount) FROM payments WHERE DATE(payment_date) = %s", (d.date(),))
            revenue.append((d.strftime("%d/%m"), to_float(cursor.fetchone()[0])))

        # Top Khách
        cursor.execute(f"""
            SELECT c.full_name, 
                   COALESCE(SUM(p.amount), 0) as total_paid
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            LEFT JOIN payments p ON i.id = p.invoice_id AND {cond}
            WHERE EXISTS (
                SELECT 1
                FROM payments p2
                WHERE p2.invoice_id = i.id
                  AND {cond}
            )
            GROUP BY c.id, c.full_name
            ORDER BY total_paid DESC
            LIMIT 5
        """, params + params)
        top_cus = [(x[0], to_float(x[1])) for x in cursor.fetchall()]

        # Top Dịch Vụ
        cursor.execute(f"""
            SELECT ii.service_name, COUNT(DISTINCT ii.invoice_id)
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            JOIN payments p ON p.invoice_id = i.id
            WHERE {cond}
            GROUP BY ii.service_name
            ORDER BY COUNT(DISTINCT ii.invoice_id) DESC
            LIMIT 8
        """, params)
        top_svc = cursor.fetchall()

        db.close()
        return cus, cars, apps, rev, revenue, top_cus, top_svc

    def update_data(self, *_):
        cus, cars, apps, rev, revenue, top_cus, top_svc = self.get_data()

        # Clear cũ
        for w in self.stat_frame.winfo_children(): w.destroy()
        for w in self.chart_frame.winfo_children(): w.destroy()

        # ===== RENDER STATS (4 ô) =====
        stats = [
            ("Tổng khách hàng", cus, "#3b82f6"),
            ("Xe trong hệ thống", cars, "#8b5cf6"),
            ("Lịch hẹn", apps, "#f59e0b"),
            ("Doanh thu kỳ", f"{rev:,.0f}đ", "#10b981")
        ]

        self.revenue_highlight_card = None
        for i, (t, v, color) in enumerate(stats):
            card = ctk.CTkFrame(self.stat_frame, fg_color="white", border_width=1, border_color="#e2e8f0", corner_radius=12)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            
            ctk.CTkLabel(card, text=t, font=("Arial", 13), text_color="#64748b").pack(pady=(15, 0))
            ctk.CTkLabel(card, text=v, font=("Arial", 22, "bold"), text_color=color).pack(pady=(5, 15))
            if t == "Doanh thu kỳ":
                self.revenue_highlight_card = card

        # ===== RENDER CHARTS =====
        # Chart 1: Doanh thu (Line)
        fig1, ax1 = plt.subplots(figsize=(5, 3.5), tight_layout=True)
        ax1.plot([x[0] for x in revenue], [x[1]/1e6 for x in revenue], marker="o", color="#3b82f6", linewidth=2)
        ax1.set_title("Xu hướng doanh thu (Triệu VNĐ)", fontsize=10, fontweight='bold')
        ax1.grid(axis='y', linestyle='--', alpha=0.6)
        self.draw(fig1, 0, 0)

        # Chart 2: Top Khách (Bar dọc)
        fig2, ax2 = plt.subplots(figsize=(5, 3.5), tight_layout=True)
        if top_cus:
            ax2.bar([x[0] for x in top_cus], [x[1]/1e6 for x in top_cus], color="#8b5cf6")
        ax2.set_title("Top 5 Khách hàng (Triệu VNĐ)", fontsize=10, fontweight='bold')
        plt.setp(ax2.get_xticklabels(), rotation=15, ha="right")
        self.draw(fig2, 0, 1)

        # Chart 3: Top Dịch vụ (Full chiều ngang)
        fig3, ax3 = plt.subplots(figsize=(10, 3.5), tight_layout=True)
        if top_svc:
            ax3.bar([x[0] for x in top_svc], [x[1] for x in top_svc], color="#10b981")
        ax3.set_title("Phân tích dịch vụ (Số lượt)", fontsize=10, fontweight='bold')
        self.draw(fig3, 1, 0, colspan=2)

    def auto_refresh(self):
        self.update_data()
        self.after(60000, self.auto_refresh)

    def draw(self, fig, r, c, colspan=1):
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        # Đặt nền trắng cho biểu đồ để tiệp màu với UI
        widget.configure(background='white')
        widget.grid(row=r, column=c, columnspan=colspan, padx=10, pady=10, sticky="nsew")