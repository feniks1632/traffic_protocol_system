import json
import os
from tkinter import filedialog
from openpyxl import Workbook

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.exceptions import Timeout, ConnectionError
from .lockable_tab import LockableTab


API_URL = "http://localhost:8000"


class InspectorTab(LockableTab):
    def __init__(self, parent, username, role):
        super().__init__("inspector", username)
        self.selected_version = None
        self.role = role
        self.frame = ttk.Frame(parent, padding=10)
        self.entries = {}
        self.build_ui()

    def load_selected_inspector_data(self):
        """Загружает актуальные данные выбранного инспектора"""
        try:
            response = requests.get(f"{API_URL}/inspectors/{self.selected_id}", timeout=3)
            if response.status_code == 200:
                inspector_data = response.json()
                self.selected_version = inspector_data["version"]

                # Заполняем поля актуальными данными
                self.entries["Фамилия"].delete(0, tk.END)
                self.entries["Фамилия"].insert(0, inspector_data["last_name"])
                self.entries["Имя"].delete(0, tk.END)
                self.entries["Имя"].insert(0, inspector_data["first_name"])
                self.entries["Отчество"].delete(0, tk.END)
                self.entries["Отчество"].insert(0, inspector_data["middle_name"])
                self.department_cb.set(inspector_data["department"])
                self.rank_cb.set(inspector_data["rank"])
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке данных инспектора)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
            self.unlock_entity()
            self.selected_id = None

    def build_ui(self):
        title = ttk.Label(
            self.frame, text="Список инспекторов", font=("Segoe UI", 14, "bold")
        )
        title.pack(anchor="w", pady=(0, 10))

        self.tree = ttk.Treeview(
            self.frame,
            columns=("ID", "Фамилия", "Имя", "Отчество", "Отдел", "Звание", "Версия"),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        if self.role == "admin":
            self.build_admin_form()

        self.load_data()

    def build_admin_form(self):
        form_frame = ttk.Frame(self.frame)
        form_frame.pack(fill="x", pady=10)

        fields = ["Фамилия", "Имя", "Отчество"]
        for i, field in enumerate(fields):
            label = ttk.Label(form_frame, text=field)
            label.grid(row=0, column=i, padx=5)
            entry = ttk.Entry(form_frame, width=15)
            entry.grid(row=1, column=i, padx=5)
            self.entries[field] = entry

        self.department_cb = ttk.Combobox(
            form_frame,
            values=["ГИБДД Центральный", "ГИБДД Восточный", "ГИБДД Северный"],
            width=20,
        )
        self.department_cb.grid(row=1, column=3, padx=5)
        self.department_cb.set("ГИБДД Центральный")

        self.rank_cb = ttk.Combobox(
            form_frame,
            values=["лейтенант", "старший лейтенант", "капитан", "майор"],
            width=15,
        )
        self.rank_cb.grid(row=1, column=4, padx=5)
        self.rank_cb.set("лейтенант")

        ttk.Label(form_frame, text="Отдел").grid(row=0, column=3)
        ttk.Label(form_frame, text="Звание").grid(row=0, column=4)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame, text="➕ Добавить инспектора", command=self.add_inspector
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="💾 Сохранить изменения", command=self.update_inspector
        ).pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_data).pack(side="left", padx=5)
        
        #экспорт данных
        ttk.Button(
        btn_frame, text="📥 Экспорт в JSON", command=self.export_inspectors_json
    ).pack(side="left", padx=5)
        
        ttk.Button(
        btn_frame, text="📊 Экспорт в Excel", command=self.export_inspectors_excel
        ).pack(side="left", padx=5)

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        try:
            response = requests.get(f"{API_URL}/inspectors", timeout=3)
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
                            row["department"],
                            row["rank"],
                            row["version"],
                        ),
                    )

            else:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось загрузить инспекторов: {response.status_code}",
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке списка инспекторов)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected or self.role != "admin":
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
            self.load_selected_inspector_data()

        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось обработать выбранную строку: {e}"
            )

    def add_inspector(self):
        last = self.entries["Фамилия"].get().strip()
        first = self.entries["Имя"].get().strip()
        middle = self.entries["Отчество"].get().strip()
        dept = self.department_cb.get().strip()
        rank = self.rank_cb.get().strip()

        if not all([last, first, middle, dept, rank]):
            messagebox.showwarning("Поля", "Заполните все поля")
            return

        data = {
            "last_name": last,
            "first_name": first,
            "middle_name": middle,
            "department": dept,
            "rank": rank,
            "user": self.username,
        }

        try:
            response = requests.post(f"{API_URL}/inspectors", json=data, timeout=3)
            if response.status_code == 201:
                messagebox.showinfo("Успех", "Инспектор добавлен")
                self.load_data()
                self.clear_form()
            elif response.status_code == 409:
                messagebox.showwarning("Конфликт", "Такой инспектор уже существует")
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось добавить инспектора: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при добавлении инспектора)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def update_inspector(self):
        if not self.selected_id:
            messagebox.showwarning("Выбор", "Выберите инспектора для редактирования")
            return
        last = self.entries["Фамилия"].get().strip()
        first = self.entries["Имя"].get().strip()
        middle = self.entries["Отчество"].get().strip()
        dept = self.department_cb.get().strip()
        rank = self.rank_cb.get().strip()

        if not all([last, first, middle, dept, rank]):
            messagebox.showwarning("Поля", "Заполните все поля")
            return

        data = {
            "last_name": last,
            "first_name": first,
            "middle_name": middle,
            "department": dept,
            "rank": rank,
            "user": self.username,
            "version": self.selected_version,
        }

        try:
            response = requests.put(
                f"{API_URL}/inspectors/{self.selected_id}", json=data, timeout=3
            )
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Инспектор обновлён")
                self.load_data()
                self.unlock_entity()
                self.clear_form()
            elif response.status_code == 404:
                messagebox.showerror("Ошибка", "Инспектор не найден")
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            elif response.status_code == 409:
                messagebox.showerror(
                    "Блокировка",
                    "Инспектор редактируется другим пользователем. Сохранение невозможно.",
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось обновить инспектора: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при обновлении инспектора)")
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
        self.department_cb.set("ГИБДД Центральный")
        self.rank_cb.set("лейтенант")

    def refresh_data(self):
        self.load_data() 
        
        
    def export_inspectors_json(self):
        try:
            response = requests.get(f"{API_URL}/reports/inspectors", timeout=5)
            if response.status_code == 200:
                self.export_to_json(response.json(), "inspectors_report.json")
            else:
                messagebox.showerror("Ошибка", f"Не удалось получить данные: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Сервер недоступен: {e}")

    def export_inspectors_excel(self):
        try:
            response = requests.get(f"{API_URL}/reports/inspectors", timeout=5)
            if response.status_code == 200:
                data = response.json()
                columns = ["id", "ФИО", "Отдел", "Звание", "Создано"]
                self.export_to_excel(data, "inspectors_report.xlsx", columns)
            else:
                messagebox.showerror("Ошибка", f"Не удалось получить данные: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Сервер недоступен: {e}")
            
    