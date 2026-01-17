import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.exceptions import Timeout, ConnectionError

from .lockable_tab import LockableTab


API_URL = "http://localhost:8000"


class OwnerTab(LockableTab):
    def __init__(self, parent, username, role):
        super().__init__("owner", username)
        self.selected_version = None
        self.role = role
        self.frame = ttk.Frame(parent, padding=10)
        self.entries = {}
        self.build_ui()

    def build_ui(self):
        title = ttk.Label(
            self.frame, text="Список владельцев", font=("Segoe UI", 14, "bold")
        )
        title.pack(anchor="w", pady=(0, 10))

        self.tree = ttk.Treeview(
            self.frame,
            columns=(
                "ID",
                "Фамилия",
                "Имя",
                "Отчество",
                "Дата рождения",
                "Адрес",
                "Версия",
            ),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        form_frame = ttk.Frame(self.frame)
        form_frame.pack(fill="x", pady=10)

        fields = ["Фамилия", "Имя", "Отчество", "Дата рождения", "Адрес"]
        for i, field in enumerate(fields):
            label = ttk.Label(form_frame, text=field)
            label.grid(row=0, column=i, padx=5)
            entry = ttk.Entry(form_frame, width=15)
            entry.grid(row=1, column=i, padx=5)
            self.entries[field] = entry

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=10)

        if self.role in ["admin", "inspector"]:
            ttk.Button(
                btn_frame, text="➕ Добавить владельца", command=self.add_owner
            ).pack(side="left", padx=5)
            ttk.Button(
                btn_frame, text="💾 Сохранить изменения", command=self.update_owner
            ).pack(side="left", padx=5)
            
            ttk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_data).pack(side="left", padx=5)
            
            # Экспорт данных
            ttk.Button(
                btn_frame, text="📥 Экспорт в JSON", command=self.export_owners_json
            ).pack(side="left", padx=5)

        self.load_owners()

    def load_owners(self):
        self.tree.delete(*self.tree.get_children())
        try:
            response = requests.get(f"{API_URL}/owners", timeout=3)
            if response.status_code == 200:
                for row in response.json():
                    self.tree.insert(
                        "",
                        "end",
                        values=(
                            row["id"],
                            row["last_name"],
                            row["first_name"],
                            row["middle_name"],
                            row["date_of_birth"],
                            row["address"],
                            row["version"],
                        ),
                    )

            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось загрузить владельцев: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке владельцов)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected or self.role not in ["admin", "inspector"]:
            return

        # Сначала разблокируем предыдущую запись
        if hasattr(self, "selected_id") and self.selected_id:
            self.unlock_entity()

        try:
            values = self.tree.item(selected[0])["values"]
            if len(values) < 7:
                raise ValueError("Недостаточно данных в строке")

            self.selected_id = values[0]

            # Сначала блокируем, потом получаем актуальные данные
            if not self.lock_entity():
                self.selected_id = None
                return

            # Загружаем актуальные данные после блокировки
            self.load_selected_owner_data()

        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось обработать выбранную строку: {e}"
            )

    def load_selected_owner_data(self):
        """Загружает актуальные данные выбранного владельца"""
        try:
            response = requests.get(f"{API_URL}/owners/{self.selected_id}", timeout=3)
            if response.status_code == 200:
                owner_data = response.json()
                self.selected_version = owner_data["version"]

                # Заполняем поля актуальными данными
                self.entries["Фамилия"].delete(0, tk.END)
                self.entries["Фамилия"].insert(0, owner_data["last_name"])
                self.entries["Имя"].delete(0, tk.END)
                self.entries["Имя"].insert(0, owner_data["first_name"])
                self.entries["Отчество"].delete(0, tk.END)
                self.entries["Отчество"].insert(0, owner_data["middle_name"])
                self.entries["Дата рождения"].delete(0, tk.END)
                self.entries["Дата рождения"].insert(0, owner_data["date_of_birth"])
                self.entries["Адрес"].delete(0, tk.END)
                self.entries["Адрес"].insert(0, owner_data["address"])
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут загрузке данных владельца)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
            self.unlock_entity()
            self.selected_id = None

    def add_owner(self):
        data = {
            "last_name": self.entries["Фамилия"].get().strip(),
            "first_name": self.entries["Имя"].get().strip(),
            "middle_name": self.entries["Отчество"].get().strip(),
            "date_of_birth": self.entries["Дата рождения"].get().strip(),
            "address": self.entries["Адрес"].get().strip(),
            "user": self.username,
        }

        if not all(data.values()):
            messagebox.showwarning("Поля", "Заполните все поля")
            return

        try:
            response = requests.post(f"{API_URL}/owners", json=data, timeout=3)
            if response.status_code == 201:
                messagebox.showinfo("Успех", "Владелец добавлен")
                self.load_owners()
                self.clear_form()
            elif response.status_code == 409:
                messagebox.showwarning("Конфликт", "Такой владелец уже существует")
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось добавить владельца: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при добавлении владельца)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def update_owner(self):
        if not self.selected_id:
            messagebox.showwarning("Выбор", "Выберите владельца для редактирования")
            return
        # try:
        #     check_response = requests.get(f"{API_URL}/owners/{self.selected_id}", timeout=3)
        #     if check_response.status_code == 200:
        #         owner_data = check_response.json()
        #         if owner_data.get("locked_by") != self.username:
        #             messagebox.showerror("Ошибка", "Вы потеряли блокировку записи")
        #             return
        # except:
        #     pass
        data = {
            "last_name": self.entries["Фамилия"].get().strip(),
            "first_name": self.entries["Имя"].get().strip(),
            "middle_name": self.entries["Отчество"].get().strip(),
            "date_of_birth": self.entries["Дата рождения"].get().strip(),
            "address": self.entries["Адрес"].get().strip(),
            "user": self.username,
            "version": self.selected_version,
        }

        if not all(data.values()):
            messagebox.showwarning("Поля", "Заполните все поля")
            return

        try:
            response = requests.put(f"{API_URL}/owners/{self.selected_id}", json=data, timeout=3)
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Данные владельца обновлены")
                self.load_owners()
                self.unlock_entity()
                self.clear_form()
            elif response.status_code == 404:
                messagebox.showerror("Ошибка", "Владелец не найден")
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            elif response.status_code == 409:
                messagebox.showerror(
                    "Блокировка",
                    "Владелец редактируется другим пользователем. Сохранение невозможно.",
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось обновить владельца: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при обновлении владельца)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def clear_form(self):
        self.unlock_entity()
        self.selected_id = None
        self.selected_version = None
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def refresh_data(self):
        self.load_owners()
        
        
    def export_owners_json(self):
        try:
            response = requests.get(f"{API_URL}/reports/owners", timeout=5)
            if response.status_code == 200:
                self.export_to_json(response.json(), "owners_report.json")
            else:
                messagebox.showerror("Ошибка", f"Не удалось получить данные: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Сервер недоступен: {e}")