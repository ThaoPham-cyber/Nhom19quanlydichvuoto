import customtkinter as ctk
# Import các class từ các file con
from gui_dashboard import DashboardFrame
from gui_customers import CustomerFrame
from gui_cars import CarFrame 
from gui_services import ServiceFrame 
from gui_inventory import InventoryFrame 
from gui_employees import EmployeeFrame
from gui_appointments import AppointmentFrame # 1. THÊM: Import file quản lý lịch hẹn mới

class AutoCareApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AutoCare Manager - Admin")
        self.geometry("1150x750") 

        # Layout chính co giãn
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (Màu nền tối #1a1a1a như thiết kế) ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Tiêu đề Sidebar
        ctk.CTkLabel(self.sidebar, text="AUTOCARE", font=("Arial", 22, "bold"), text_color="#2563eb").pack(pady=30)

        # --- KHUNG CHỨA CÁC TRANG (Phần bên phải) ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        # 2. CẬP NHẬT: Thêm AppointmentFrame vào danh sách khởi tạo
        pages = (
            DashboardFrame, CustomerFrame, CarFrame, 
            ServiceFrame, InventoryFrame, EmployeeFrame, 
            AppointmentFrame # Thêm ở đây
        )

        for F in pages:
            page_name = F.__name__
            frame = F(parent=self.container)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # --- NÚT ĐIỀU HƯỚNG SIDEBAR ---
        self.create_nav_button("Tổng quan", "DashboardFrame")
        self.create_nav_button("Lịch hẹn", "AppointmentFrame") # 3. THÊM: Nút lịch hẹn đặt ở vị trí ưu tiên
        self.create_nav_button("Khách hàng", "CustomerFrame")
        self.create_nav_button("Xe", "CarFrame")
        self.create_nav_button("Dịch vụ", "ServiceFrame")
        self.create_nav_button("Kho hàng", "InventoryFrame")
        self.create_nav_button("Nhân viên", "EmployeeFrame") 

        # Mặc định mở trang Tổng quan khi vừa bật app
        self.show_frame("DashboardFrame")

    def create_nav_button(self, text, page_name):
        """Hàm hỗ trợ tạo nút menu nhanh với hiệu ứng hover"""
        btn = ctk.CTkButton(self.sidebar, text=text, height=45,
                            fg_color="transparent", 
                            text_color="white",
                            hover_color="#333333",
                            anchor="w",
                            font=("Arial", 13),
                            command=lambda: self.show_frame(page_name))
        btn.pack(pady=5, padx=20, fill="x")

    def show_frame(self, page_name):
        """Hàm chuyển đổi giữa các trang"""
        if page_name in self.frames:
            frame = self.frames[page_name]
            frame.tkraise()
            
            # 4. Tự động tải lại dữ liệu mới nhất khi bấm vào trang
            # Kiểm tra xem class có hàm load tương ứng không để cập nhật UI
            if hasattr(frame, 'load_data'):
                frame.load_data()
            elif hasattr(frame, 'load_services'):
                frame.load_services()
            elif hasattr(frame, 'load_inventory'): 
                frame.load_inventory()
            elif hasattr(frame, 'load_employees'): 
                frame.load_employees()
            # THÊM: Cập nhật danh sách lịch hẹn khi bấm vào menu
            elif hasattr(frame, 'load_appointments'): 
                frame.load_appointments()
        else:
            print(f"Lỗi: Không tìm thấy trang {page_name}")

if __name__ == "__main__":
    app = AutoCareApp()
    app.mainloop()