"""Application entry point for the Student Management System."""

from config.config import APP_NAME, DATABASE_PATH
from database.database import initialize_database
from ui.app import LoginWindow


def main() -> None:
    """Initialize persistent storage and open the authenticated desktop UI."""
    initialize_database()
    import tkinter as tk
    from tkinter import ttk
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("1180x720")
    root.minsize(980, 620)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#17365D")
    style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"))
    style.configure("Card.TLabel", font=("Segoe UI", 18, "bold"), foreground="#1F4E79")
    style.configure("Side.TFrame", background="#17365D")
    style.configure("SideTitle.TLabel", background="#17365D", foreground="white", font=("Segoe UI", 20, "bold"))
    style.configure("Side.TButton", padding=9)
    def open_application() -> None:
        for child in root.winfo_children():
            child.destroy()
        from ui.app import MainApplication
        MainApplication(root)

    LoginWindow(root, open_application).pack(expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
