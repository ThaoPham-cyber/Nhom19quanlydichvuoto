import customtkinter as ctk
from gui_services import ServiceFrame 
from gui_inventory import InventoryFrame 


class AutoCareApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AutoCare Manager - Admin")
        self.geometry("1150x750")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ===== SIDEBAR =====
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            self.sidebar,
            text="AUTOCARE",
            font=("Arial", 22, "bold"),
            text_color="#2563eb"
        ).pack(pady=30)

        # ===== CONTAINER =====
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew")

        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}

        pages = (
           
            ServiceFrame,
            InventoryFrame,
            
        )

        # 🔴 FIX QUAN TRỌNG Ở ĐÂY
        for F in pages:
            page_name = F.__name__

            frame = F(self.container)   # ✅ KHÔNG dùng parent=
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        # ===== NAV BUTTON =====
        self.create_nav_button("Dịch vụ", "ServiceFrame")
        self.create_nav_button("Kho hàng", "InventoryFrame")
        self.show_frame("DashboardFrame")

    # ================= NAV =================
    def create_nav_button(self, text, page_name):
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            height=45,
            fg_color="transparent",
            text_color="white",
            hover_color="#333333",
            anchor="w",
            font=("Arial", 13),
            command=lambda: self.show_frame(page_name)
        )
        btn.pack(pady=5, padx=20, fill="x")

    # ================= SWITCH PAGE =================
    def show_frame(self, page_name):
        if page_name in self.frames:
            frame = self.frames[page_name]
            frame.tkraise()

            # ===== AUTO RELOAD =====
            if hasattr(frame, "load"):
                frame.load()
            elif hasattr(frame, "load_data"):
                frame.load_data()
            elif hasattr(frame, "load_services"):
                frame.load_services()
            elif hasattr(frame, "load_inventory"):
                frame.load_inventory()
            elif hasattr(frame, "load_employees"):
                frame.load_employees()

        else:
            print(f"Lỗi: Không tìm thấy trang {page_name}")


if __name__ == "__main__":
    app = AutoCareApp()
    app.mainloop()