import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.exceptions import Timeout, ConnectionError
from .lockable_tab import LockableTab


API_URL = "http://localhost:8000"


class ViolationTab(LockableTab):
    def __init__(self, parent, username, role):
        super().__init__("violation", username)
        self.selected_version = None
        self.role = role
        self.frame = ttk.Frame(parent, padding=10)
        self.entries = {}
        self.build_ui()

    def build_ui(self):
        title = ttk.Label(
            self.frame, text="Справочник нарушений", font=("Segoe UI", 14, "bold")
        )
        title.pack(anchor="w", pady=(0, 10))

        filter_frame = ttk.Frame(self.frame)
        filter_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_frame, text="Тип нарушения").pack(side="left", padx=(0, 5))
        self.type_cb = ttk.Combobox(filter_frame, width=30)
        self.type_cb.pack(side="left", padx=(0, 10))
        self.type_cb.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        reset_btn = ttk.Button(
            filter_frame, text="🔄 Показать все", command=self.reset_filter
        )
        reset_btn.pack(side="left")

        self.tree = ttk.Treeview(
            self.frame,
            columns=("ID", "Нарушение", "Тип", "Статья", "Версия"),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=250, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        if self.role in ["admin", "inspector"]:
            self.build_admin_form()

        self.load_types()
        self.load_data()

    def build_admin_form(self):
        form_frame = ttk.Frame(self.frame)
        form_frame.pack(fill="x", pady=10)

        fields = ["Нарушение", "Тип", "Статья №", "Название статьи"]
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=field).grid(row=0, column=i, padx=5)
            entry = ttk.Entry(form_frame, width=20)
            entry.grid(row=1, column=i, padx=5)
            self.entries[field] = entry

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame, text="➕ Добавить нарушение", command=self.add_violation
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="💾 Сохранить изменения", command=self.update_violation
        ).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_data).pack(side="left", padx=5)

        ttk.Button(
            btn_frame, text="📥 Экспорт в JSON", command=self.export_violation_json
            ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="📊 Экспорт в Excel", command=self.export_violation_excel
        ).pack(side="left", padx=5)

    def load_types(self):
        try:
            response = requests.get(f"{API_URL}/violations/violation-types", timeout=3)
            if response.status_code == 200:
                types = [t["name"] for t in response.json()]
                self.type_cb["values"] = types
            else:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось загрузить типы нарушений: {response.status_code}",
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке типов нарушений)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        try:
            if self.type_cb.get():
                response = requests.get(
                    f"{API_URL}/violations", params={"type": self.type_cb.get()}, timeout=3
                )
            else:
                response = requests.get(f"{API_URL}/violations", timeout=3)

            if response.status_code == 200:
                for row in response.json():
                    self.tree.insert(
                        "",
                        "end",
                        values=(
                            row["id"],
                            row["name"],
                            row["type"],
                            f"{row['article_number']} — {row['article_name']}",
                            row["version"],
                        ),
                    )

            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось загрузить нарушения: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке списка нарушений)")
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
            if len(values) < 5:
                raise ValueError("Недостаточно данных в строке")

            self.selected_id = values[0]  # ID нарушения

            # Сначала блокируем, потом получаем актуальные данные
            if not self.lock_entity():
                self.selected_id = None
                return

            # Загружаем актуальные данные после блокировки
            self.load_selected_violation_data()

        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось обработать выбранную строку: {e}"
            )

    def load_selected_violation_data(self):
        """Загружает актуальные данные выбранного нарушения"""
        try:
            response = requests.get(f"{API_URL}/violations/{self.selected_id}",timeout=3)
            if response.status_code == 200:
                violation_data = response.json()
                self.selected_version = violation_data["version"]

                # Заполняем поля актуальными данными
                self.entries["Нарушение"].delete(0, tk.END)
                self.entries["Нарушение"].insert(0, violation_data["name"])

                self.entries["Тип"].delete(0, tk.END)
                self.entries["Тип"].insert(0, violation_data["type"])

                self.entries["Статья №"].delete(0, tk.END)
                self.entries["Статья №"].insert(0, violation_data["article_number"])

                self.entries["Название статьи"].delete(0, tk.END)
                self.entries["Название статьи"].insert(
                    0, violation_data["article_name"]
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке данных нарушения)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
            self.unlock_entity()
            self.selected_id = None

    def add_violation(self):
        data = self.collect_data()
        if not data:
            return

        try:
            response = requests.post(f"{API_URL}/violations", json=data, timeout=3)
            if response.status_code == 201:
                messagebox.showinfo("Успех", "Нарушение добавлено")
                self.load_data()
                self.clear_form()
            elif response.status_code == 409:
                messagebox.showwarning("Конфликт", "Такое нарушение уже существует")
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось добавить нарушение: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при добавлении нарушения)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def update_violation(self):
        if not self.selected_id:
            messagebox.showwarning("Выбор", "Выберите нарушение для редактирования")
            return

        data = self.collect_data()
        if not data:
            return

        try:
            response = requests.put(
                f"{API_URL}/violations/{self.selected_id}", json=data, timeout=3
            )
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Нарушение обновлено")
                self.load_data()
                self.unlock_entity()
                self.clear_form()
            elif response.status_code == 404:
                messagebox.showerror("Ошибка", "Нарушение не найдено")
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            elif response.status_code == 409:
                messagebox.showerror(
                    "Блокировка",
                    "Нарушение редактируется другим пользователем. Сохранение невозможно.",
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось обновить нарушение: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при обновлении нарушения)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def collect_data(self):
        name = self.entries["Нарушение"].get().strip()
        type_name = self.entries["Тип"].get().strip()
        article_number = self.entries["Статья №"].get().strip()
        article_name = self.entries["Название статьи"].get().strip()

        if not all([name, type_name, article_number, article_name]):
            messagebox.showwarning("Поля", "Заполните все поля")
            return None

        data = {
            "name": name,
            "type": type_name,
            "article_number": article_number,
            "article_name": article_name,
            "user": self.username,
        }

        # Добавляем версию только для обновления
        if hasattr(self, "selected_version") and self.selected_version is not None:
            data["version"] = self.selected_version

        return data

    def clear_form(self):
        self.unlock_entity()
        self.selected_id = None
        self.selected_version = None
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def reset_filter(self):
        self.type_cb.set("")
        self.load_data()


    def refresh_data(self):
        self.load_data()
        
    
    def export_violation_json(self):
        try:
            response = requests.get(f"{API_URL}/reports/violations", timeout=5)
            if response.status_code == 200:
                self.export_to_json(response.json(), "violations_report.json")
            else:
                messagebox.showerror("Ошибка", f"Не удалось получить данные: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Сервер недоступен: {e}")

    def export_violation_excel(self):
        try:
            response = requests.get(f"{API_URL}/reports/violations", timeout=5)
            if response.status_code == 200:
                data = response.json()
                columns = ["id", "Название", "Тип нарушения", "Создано"]
                self.export_to_excel(data, "violations_report.xlsx", columns)
            else:
                messagebox.showerror("Ошибка", f"Не удалось получить данные: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Сервер недоступен: {e}")