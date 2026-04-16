import customtkinter as ctk
from database import connect_db
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f5f5f5", corner_radius=0)
        
        # Cấu hình co giãn cho Dashboard
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Tiêu đề
        header = ctk.CTkLabel(self, text="Tổng quan hệ thống", font=("Arial", 28, "bold"), text_color="black")
        header.grid(row=0, column=0, padx=30, pady=20, sticky="w")

        # Container chứa các Card thông số
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=20)
        self.create_cards()

    def create_cards(self):
        # Giả lập dữ liệu hoặc lấy từ database.py
        cards = [
            ("Khách hàng", "150", "#2563eb"),
            ("Xe quản lý", "85", "#059669"),
            ("Doanh thu", "67tr", "#7c3aed")
        ]
        for i, (title, val, color) in enumerate(cards):
            card = ctk.CTkFrame(self.stats_frame, fg_color="white", corner_radius=15, width=200, height=100)
            card.pack_propagate(False)
            card.pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(card, text=title, text_color="gray").pack(pady=(10,0))
            ctk.CTkLabel(card, text=val, font=("Arial", 24, "bold"), text_color=color).pack()