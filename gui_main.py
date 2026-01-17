import tkinter as tk
from tkinter import ttk
from ui.owner_tab import OwnerTab
from ui.inspector_tab import InspectorTab
from ui.vehicle_tab import VehicleTab
from ui.violation_tab import ViolationTab
from ui.protocol_tab import ProtocolTab


def launch_main(username, role):
    root = tk.Tk()
    root.title(f"🚦 Система контроля правонарушений — {username}")
    root.geometry("1000x700")
    root.configure(bg="#f0f2f5")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook.Tab", padding=[12, 8], font=("Segoe UI", 11, "bold"))
    style.configure("TLabel", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10), padding=6)
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
    style.map("TNotebook.Tab", background=[("selected", "#d0e0ff")])

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    # Вкладки с передачей username и role
    owner_tab = OwnerTab(notebook, username, role)
    inspector_tab = InspectorTab(notebook, username, role)
    vehicle_tab = VehicleTab(notebook, username, role)
    violation_tab = ViolationTab(notebook, username, role)
    protocol_tab = ProtocolTab(notebook, username, role)

    notebook.add(owner_tab.frame, text="👤 Владельцы")
    notebook.add(inspector_tab.frame, text="👮 Инспекторы")
    notebook.add(vehicle_tab.frame, text="🚘 ТС")
    notebook.add(violation_tab.frame, text="⚠️ Нарушения")
    notebook.add(protocol_tab.frame, text="📄 Протоколы")

    # Словарь вкладок
    # tabs = {
    #     notebook.tabs()[0]: owner_tab,
    #     notebook.tabs()[1]: inspector_tab,
    #     notebook.tabs()[2]: vehicle_tab,
    #     notebook.tabs()[3]: violation_tab,
    #     notebook.tabs()[4]: protocol_tab,
    # }
    
    frame_to_tab = {
        owner_tab.frame: owner_tab,
        inspector_tab.frame: inspector_tab,
        vehicle_tab.frame: vehicle_tab,
        violation_tab.frame: violation_tab,
        protocol_tab.frame: protocol_tab,
    }
    
    current_tab = [owner_tab]

    # Текущая активная вкладка
    current_tab = [owner_tab]

    # Обработчик переключения вкладок
    def on_tab_changed(event):
        # selected_tab_id = notebook.select() по фреймам было по словарю
        selected_frame = notebook.nametowidget(notebook.select())
        new_tab = frame_to_tab.get(selected_frame)

        if current_tab[0] and hasattr(current_tab[0], "on_tab_switch"):
            print(f"[TAB SWITCH] Снимаем блокировку с {current_tab[0].entity_type}")
            current_tab[0].on_tab_switch()
        
                # ← Автоматически обновляем данные при входе на вкладку
        if new_tab and hasattr(new_tab, "refresh_data"):
            new_tab.refresh_data()
            
        current_tab[0] = new_tab

    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    root.mainloop()
