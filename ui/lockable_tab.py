import json
from openpyxl import Workbook
import requests
from tkinter import filedialog, messagebox

API_URL = "http://localhost:8000"


class LockableTab:
    def __init__(self, entity_type, username):
        self.entity_type = entity_type
        self.username = username
        self.selected_id = None
        self.locked = False


    def lock_entity(self):
        if not self.selected_id:
            return False
        try:
            url = f"{API_URL}/lock/{self.entity_type}/{self.selected_id}"
            response = requests.post(url, params={"user": self.username})

            if response.status_code == 200:
                return True
            elif response.status_code == 409:
                messagebox.showerror(
                    "Блокировка",
                    f"{self.entity_type.upper()} редактируется другим пользователем",
                )
                return False
            else:
                messagebox.showerror(
                    "Ошибка", f"Ошибка блокировки: {response.status_code}"
                )
                return False
        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось захватить {self.entity_type}: {e}"
            )
            return False

    def unlock_entity(self):
        if not self.selected_id:
            return
        try:
            url = f"{API_URL}/unlock/{self.entity_type}/{self.selected_id}"
            response = requests.post(url, params={"user": self.username})

            if response.status_code != 200:
                print(f"[UNLOCK WARNING] {response.status_code}")
        except Exception as e:
            print(f"[UNLOCK ERROR] {e}")

    def on_tab_switch(self):
        self.unlock_entity()
        
    def refresh_data(self):
        """
        Метод для обновления данных. Должен быть переопределён в дочерних классах.
        По умолчанию — ничего не делает.
        """
        pass

    def export_to_json(self, data, default_filename):
        """Экспорт данных в JSON"""
        file_path = filedialog.asksaveasfilename(
            title="Сохранить отчёт как JSON",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
            initialfile=default_filename
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Успех", f"Отчёт сохранён:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
                
    def export_to_excel(self, data, default_filename, columns):
        """Экспорт плоских данных в Excel"""
        file_path = filedialog.asksaveasfilename(
            title="Сохранить отчёт как Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")],
            initialfile=default_filename
        )
        if file_path:
            try:
                wb = Workbook()
                ws = wb.active
                ws.append(columns)  # заголовки

                for item in data:
                    row = [item.get(col, "") for col in columns]
                    ws.append(row)

                wb.save(file_path)
                messagebox.showinfo("Успех", f"Отчёт сохранён:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить Excel:\n{e}")            