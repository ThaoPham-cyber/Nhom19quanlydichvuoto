import customtkinter as ctk

class AutoCareApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AutoCare Manager - Admin Dashboard")
        self.geometry("1100x600")

        # Cấu hình Layout 1x2 (Sidebar x Main)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AutoCare Manager", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20)

        # Các nút Menu
        buttons = ["Tổng quan", "Khách hàng", "Xe", "Dịch vụ", "Lịch hẹn", "Kho hàng", "Nhân viên"]
        for btn_text in buttons:
            btn = ctk.CTkButton(self.sidebar_frame, text=btn_text, fg_color="transparent", text_color=("gray10", "gray90"), anchor="w")
            btn.pack(fill="x", padx=10, pady=5)

        # 2. Main Frame (Nơi hiển thị nội dung từng mục)
        self.main_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.show_dashboard()

    def show_dashboard(self):
        # Tiêu đề Dashboard
        title = ctk.CTkLabel(self.main_frame, text="Tổng quan", font=ctk.CTkFont(size=24, weight="bold"), text_color="black")
        title.pack(anchor="w", padx=20, pady=10)
        
        # Ví dụ Card thống kê (Dùng Frame con)
        card = ctk.CTkFrame(self.main_frame, width=200, height=100, fg_color="white")
        card.pack(side="left", padx=20, pady=20)
        lbl = ctk.CTkLabel(card, text="Tổng khách hàng\n487", text_color="black")
        lbl.place(relx=0.5, rely=0.5, anchor="center")

if __name__ == "__main__":
    app = AutoCareApp()
    app.mainloop()