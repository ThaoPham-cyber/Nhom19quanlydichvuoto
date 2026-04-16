import customtkinter as ctk
# Import các class từ các file con
from gui_dashboard import DashboardFrame
from gui_customers import CustomerFrame
# Lưu ý: Import CarFrame để làm trang hiển thị chính, không phải AddCarWindow
from gui_cars import CarFrame 

class AutoCareApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AutoCare Manager - Admin")
        self.geometry("1100x700")

        # Layout chính co giãn
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Tiêu đề Sidebar
        ctk.CTkLabel(self.sidebar, text="AUTOCARE", font=("Arial", 22, "bold"), text_color="#2563eb").pack(pady=30)

        # --- KHUNG CHỨA CÁC TRANG (Phần bên phải) ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        # KHỞI TẠO CÁC TRANG: Dashboard, Khách hàng và Xe
        # Thao thêm CarFrame vào danh sách này nhé
        for F in (DashboardFrame, CustomerFrame, CarFrame):
            page_name = F.__name__
            frame = F(parent=self.container)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # --- NÚT ĐIỀU HƯỚNG SIDEBAR ---
        self.create_nav_button("Tổng quan", "DashboardFrame")
        self.create_nav_button("Khách hàng", "CustomerFrame")
        self.create_nav_button("Xe", "CarFrame") # Nút Xe trỏ về trang CarFrame

        # Mặc định mở trang Tổng quan khi vừa bật app
        self.show_frame("DashboardFrame")

    def create_nav_button(self, text, page_name):
        """Hàm hỗ trợ tạo nút menu nhanh"""
        btn = ctk.CTkButton(self.sidebar, text=text, height=40,
                           fg_color="transparent", anchor="w",
                           command=lambda: self.show_frame(page_name))
        btn.pack(pady=5, padx=20, fill="x")

    def show_frame(self, page_name):
        """Hàm chuyển đổi giữa các trang"""
        if page_name in self.frames:
            frame = self.frames[page_name]
            frame.tkraise()
            # Tự động tải lại dữ liệu mới nhất khi bấm vào trang
            if hasattr(frame, 'load_data'):
                frame.load_data()
        else:
            print(f"Lỗi: Không tìm thấy trang {page_name}")

if __name__ == "__main__":
    app = AutoCareApp()
    app.mainloop()