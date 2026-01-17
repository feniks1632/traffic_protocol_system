import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.exceptions import Timeout, ConnectionError
from .lockable_tab import LockableTab


API_URL = "http://localhost:8000"


class ProtocolTab(LockableTab):
    def __init__(self, parent, username, role):
        super().__init__("protocol", username)
        self.selected_version = None
        self.role = role
        self.frame = ttk.Frame(parent, padding=10)
        self.entries = {}
        self.build_ui()

    def build_ui(self):
        title = ttk.Label(
            self.frame, text="Протоколы правонарушений", font=("Segoe UI", 14, "bold")
        )
        title.pack(anchor="w", pady=(0, 10))

        self.tree = ttk.Treeview(
            self.frame,
            columns=(
                "ID",
                "Номер",
                "Дата",
                "Время",
                "ТС",
                "Владелец",
                "Инспектор",
                "Нарушение",
                "Версия",
            ),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        # Скрываем колонку ID
        self.tree.column("ID", width=0, stretch=False)
        self.tree.heading("ID", text="")

        self.tree.pack(fill="both", expand=True, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        form_frame = ttk.Frame(self.frame)
        form_frame.pack(fill="x", pady=10)

        self.entries["Номер"] = ttk.Entry(form_frame, width=12)
        self.entries["Номер"].grid(row=1, column=0, padx=5)
        ttk.Label(form_frame, text="Номер").grid(row=0, column=0, padx=5)

        self.entries["Дата"] = ttk.Entry(form_frame, width=12)
        self.entries["Дата"].grid(row=1, column=1, padx=5)
        ttk.Label(form_frame, text="Дата").grid(row=0, column=1, padx=5)

        self.entries["Время"] = ttk.Entry(form_frame, width=10)
        self.entries["Время"].grid(row=1, column=2, padx=5)
        ttk.Label(form_frame, text="Время").grid(row=0, column=2, padx=5)

        self.vehicle_cb = ttk.Combobox(form_frame, width=15)
        self.vehicle_cb.grid(row=1, column=3, padx=5)
        ttk.Label(form_frame, text="ТС").grid(row=0, column=3, padx=5)

        self.owner_cb = ttk.Combobox(form_frame, width=20)
        self.owner_cb.grid(row=1, column=4, padx=5)
        ttk.Label(form_frame, text="Владелец").grid(row=0, column=4, padx=5)

        self.inspector_cb = ttk.Combobox(form_frame, width=20)
        self.inspector_cb.grid(row=1, column=5, padx=5)
        ttk.Label(form_frame, text="Инспектор").grid(row=0, column=5, padx=5)

        self.violation_cb = ttk.Combobox(form_frame, width=30)
        self.violation_cb.grid(row=1, column=6, padx=5)
        ttk.Label(form_frame, text="Нарушение").grid(row=0, column=6, padx=5)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=10)

        if self.role in ["admin", "inspector"]:
            ttk.Button(
                btn_frame, text="➕ Добавить протокол", command=self.add_protocol
            ).pack(side="left", padx=5)
            ttk.Button(
                btn_frame, text="💾 Сохранить изменения", command=self.update_protocol
            ).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_data).pack(side="left", padx=5)

        self.load_comboboxes()
        self.load_data()

    def load_comboboxes(self):
        try:
            self.vehicle_cb["values"] = [
                v["state_number"] for v in requests.get(f"{API_URL}/vehicles", timeout=3).json()
            ]
            self.owner_cb["values"] = [
                f"{o['last_name']} {o['first_name']}"
                for o in requests.get(f"{API_URL}/owners", timeout=3).json()
            ]
            self.inspector_cb["values"] = [
                f"{i['last_name']} {i['first_name']}"
                for i in requests.get(f"{API_URL}/inspectors", timeout=3).json()
            ]
            self.violation_cb["values"] = [
                v["name"] for v in requests.get(f"{API_URL}/violations", timeout=3).json()
            ]
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке справочников)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить справочники: {e}")

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        try:
            response = requests.get(f"{API_URL}/protocols", timeout=3)
            for row in response.json():
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        row["id"],
                        row["number"],
                        row["issue_date"],
                        row["issue_time"],
                        row["vehicle"],
                        row["owner"],
                        row["inspector"],
                        row["violation"],
                        row["version"],
                    ),
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке протоколов)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить протоколы: {e}")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected or self.role not in ["admin", "inspector"]:
            return

        # Сначала разблокируем предыдущую запись
        if hasattr(self, "selected_id") and self.selected_id:
            self.unlock_entity()

        try:
            values = self.tree.item(selected[0])["values"]
            if len(values) < 9:  # Теперь 9 колонок
                raise ValueError("Недостаточно данных в строке")

            self.selected_id = values[0]  # ← Теперь это ID (число)

            # Сначала блокируем, потом получаем актуальные данные
            if not self.lock_entity():
                self.selected_id = None
                return

            # Загружаем актуальные данные после блокировки
            self.load_selected_protocol_data()

        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось обработать выбранную строку: {e}"
            )

    def load_selected_protocol_data(self):
        """Загружает актуальные данные выбранного протокола"""
        try:
            response = requests.get(f"{API_URL}/protocols/{self.selected_id}", timeout=3)
            if response.status_code == 200:
                protocol_data = response.json()
                self.selected_version = protocol_data["version"]

                # Заполняем поля актуальными данными
                self.entries["Номер"].delete(0, tk.END)
                self.entries["Номер"].insert(0, protocol_data["number"])
                self.entries["Дата"].delete(0, tk.END)
                self.entries["Дата"].insert(0, protocol_data["issue_date"])
                self.entries["Время"].delete(0, tk.END)
                self.entries["Время"].insert(0, protocol_data["issue_time"])
                self.vehicle_cb.set(protocol_data["vehicle"])
                self.owner_cb.set(protocol_data["owner"])
                self.inspector_cb.set(protocol_data["inspector"])
                self.violation_cb.set(protocol_data["violation"])
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке протокола)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
            self.unlock_entity()
            self.selected_id = None

    def add_protocol(self):
        data = self.collect_data()
        if not data:
            return

        try:
            response = requests.post(f"{API_URL}/protocols", json=data, timeout=3)
            if response.status_code == 201:
                messagebox.showinfo("Успех", "Протокол добавлен")
                self.load_data()
                self.clear_form()
            elif response.status_code == 409:
                messagebox.showwarning(
                    "Конфликт", "Протокол с таким номером уже существует"
                )
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось добавить протокол: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при добавлении протокола)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def update_protocol(self):
        if not self.selected_id:
            messagebox.showwarning("Выбор", "Выберите протокол для редактирования")
            return

        data = self.collect_data()
        if not data:
            return

        try:
            # Используем ID вместо номера протокола
            response = requests.put(
                f"{API_URL}/protocols/{self.selected_id}", json=data, timeout=3
            )
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Протокол обновлён")
                self.load_data()
                self.unlock_entity()
                self.clear_form()
            elif response.status_code == 404:
                messagebox.showerror("Ошибка", "Протокол не найден")
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            elif response.status_code == 409:
                messagebox.showerror(
                    "Блокировка",
                    "Протокол редактируется другим пользователем. Сохранение невозможно.",
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось обновить протокол: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при обновлении протокола)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def collect_data(self):
        number = self.entries["Номер"].get().strip()
        date = self.entries["Дата"].get().strip()
        time = self.entries["Время"].get().strip()
        vehicle = self.vehicle_cb.get().strip()
        owner = self.owner_cb.get().strip()
        inspector = self.inspector_cb.get().strip()
        violation = self.violation_cb.get().strip()

        if not all([number, date, time, vehicle, owner, inspector, violation]):
            messagebox.showwarning("Поля", "Заполните все поля")
            return None

        data = {
            "number": number,
            "issue_date": date,
            "issue_time": time,
            "vehicle": vehicle,
            "owner": owner,
            "inspector": inspector,
            "violation": violation,
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
        self.vehicle_cb.set("")
        self.owner_cb.set("")
        self.inspector_cb.set("")
        self.violation_cb.set("")

    def refresh_data(self):
        self.load_data()