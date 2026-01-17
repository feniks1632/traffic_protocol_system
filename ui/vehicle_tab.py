import tkinter as tk
from tkinter import ttk, messagebox
import requests
from requests.exceptions import Timeout, ConnectionError
from .lockable_tab import LockableTab

API_URL = "http://localhost:8000"


class VehicleTab(LockableTab):
    def __init__(self, parent, username, role):
        super().__init__("vehicle", username)
        self.selected_version = None
        self.role = role
        self.frame = ttk.Frame(parent, padding=10)
        self.build_ui()
        self.load_comboboxes()

    def build_ui(self):
        title = ttk.Label(
            self.frame,
            text="Список транспортных средств",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(anchor="w", pady=(0, 10))

        self.tree = ttk.Treeview(
            self.frame,
            columns=("ID", "Гос. номер", "Модель", "Цвет", "Владелец", "Версия"),
            show="headings",
        )
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.column("ID", width=0, stretch=False)
        self.tree.heading("ID", text="")
        self.tree.pack(fill="both", expand=True, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        form_frame = ttk.Frame(self.frame)
        form_frame.pack(fill="x", pady=10)

        ttk.Label(form_frame, text="Гос. номер").grid(row=0, column=0, padx=5)
        self.state_entry = ttk.Entry(form_frame, width=15)
        self.state_entry.grid(row=1, column=0, padx=5)

        ttk.Label(form_frame, text="Модель").grid(row=0, column=1, padx=5)
        self.model_cb = ttk.Combobox(form_frame, width=20)
        self.model_cb.grid(row=1, column=1, padx=5)

        ttk.Label(form_frame, text="Цвет").grid(row=0, column=2, padx=5)
        self.color_cb = ttk.Combobox(form_frame, width=15)
        self.color_cb.grid(row=1, column=2, padx=5)

        ttk.Label(form_frame, text="Владелец").grid(row=0, column=3, padx=5)
        self.owner_cb = ttk.Combobox(form_frame, width=20)
        self.owner_cb.grid(row=1, column=3, padx=5)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=10)

        if self.role in ["admin", "inspector"]:
            ttk.Button(btn_frame, text="➕ Добавить ТС", command=self.add_vehicle).pack(
                side="left", padx=5
            )
            ttk.Button(
                btn_frame, text="💾 Сохранить изменения", command=self.update_vehicle
            ).pack(side="left", padx=5)
            ttk.Button(
                btn_frame, text="🗑 Удалить ТС", command=self.delete_vehicle
            ).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_data).pack(side="left", padx=5)

        self.load_vehicles()

    def load_comboboxes(self):
        try:
            models = requests.get(f"{API_URL}/vehicles/models", timeout=3).json()
            self.model_cb["values"] = [f"{m['name']} ({m['brand']})" for m in models]

            colors = requests.get(f"{API_URL}/vehicles/colors", timeout=3).json()
            self.color_cb["values"] = [c["name"] for c in colors]

            owners_resp = requests.get(f"{API_URL}/owners", timeout=3)
            if owners_resp.status_code == 200:
                owners = owners_resp.json()
                if isinstance(owners, list):
                    self.owner_cb["values"] = [
                        f"{o['last_name']} {o['first_name']}" for o in owners
                    ]
                else:
                    raise ValueError("Ответ по владельцам не является списком")
            else:
                raise ValueError(f"Ошибка загрузки владельцев: {owners_resp.status_code}")
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке справочников)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные данные: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def load_vehicles(self):
        self.tree.delete(*self.tree.get_children())
        try:
            response = requests.get(f"{API_URL}/vehicles", timeout=3)
            if response.status_code == 200:
                for row in response.json():
                    # Вставляем ID как первое значение
                    self.tree.insert(
                        "",
                        "end",
                        values=(
                            row["id"],  # ← ID
                            row["state_number"],
                            row["model"],
                            row["color"],
                            row["owner"],
                            row["version"],
                        ),
                    )
            else:
                messagebox.showerror("Ошибка", f"Не удалось загрузить ТС: {response.status_code}")
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке списка)")
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
            if len(values) < 6:  # Теперь 6 колонок
                raise ValueError("Недостаточно данных в строке")

            self.selected_id = values[0]  # ← Теперь это ID (число)

            # Сначала блокируем, потом получаем актуальные данные
            if not self.lock_entity():
                self.selected_id = None
                return

            # Загружаем актуальные данные после блокировки
            self.load_selected_vehicle_data()

        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось обработать выбранную строку: {e}"
            )

    def load_selected_vehicle_data(self):
        """Загружает актуальные данные выбранного ТС"""
        try:
            response = requests.get(f"{API_URL}/vehicles/{self.selected_id}", timeout=3)
            if response.status_code == 200:
                vehicle_data = response.json()
                self.selected_version = vehicle_data["version"]

                # Заполняем поля актуальными данными
                self.state_entry.delete(0, tk.END)
                self.state_entry.insert(0, vehicle_data["state_number"])
                self.model_cb.set(vehicle_data["model"])
                self.color_cb.set(vehicle_data["color"])
                self.owner_cb.set(vehicle_data["owner"])

            else:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {response.status_code}")
                self.unlock_entity()
                self.selected_id = None
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при загрузке данных)")
            self.unlock_entity()
            self.selected_id = None
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            self.unlock_entity()
            self.selected_id = None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")
            self.unlock_entity()
            self.selected_id = None

    def add_vehicle(self):
        state_number = self.state_entry.get().strip()
        model_text = self.model_cb.get().strip()
        color_text = self.color_cb.get().strip()
        owner_text = self.owner_cb.get().strip()

        if not all([state_number, model_text, color_text, owner_text]):
            messagebox.showwarning("Поля", "Заполните все поля")
            return

        try:
            if " (" not in model_text or not owner_text.count(" ") == 1:
                messagebox.showerror("Ошибка", "Неверный формат модели или владельца")
                return
            model_name = model_text.split(" (")[0]
            brand_name = model_text.split(" (")[1][:-1]
            last_name, first_name = owner_text.split(" ")
        except Exception:
            messagebox.showerror("Ошибка", "Неверный формат модели или владельца")
            return

        data = {
            "state_number": state_number,
            "model_name": model_name,
            "brand_name": brand_name,
            "color_name": color_text,
            "owner_last_name": last_name,
            "owner_first_name": first_name,
            "user": self.username,
        }

        try:
                response = requests.post(f"{API_URL}/vehicles", json=data, timeout=5)
                if response.status_code == 201:
                    messagebox.showinfo("Успех", "ТС добавлено")
                    self.load_vehicles()
                    self.clear_form()
                elif response.status_code == 409:
                    messagebox.showwarning("Конфликт", "ТС с таким номером уже существует")
                elif response.status_code == 422:
                    messagebox.showerror(
                        "Ошибка валидации",
                        str(response.json().get("detail", "Некорректные данные")),
                    )
                else:
                    messagebox.showerror("Ошибка", f"Не удалось добавить ТС: {response.status_code}")
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при добавлении)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def update_vehicle(self):
        if not self.selected_id:
            messagebox.showwarning("Выбор", "Выберите ТС для редактирования")
            return

        state_number = self.state_entry.get().strip()
        model_text = self.model_cb.get().strip()
        color_text = self.color_cb.get().strip()
        owner_text = self.owner_cb.get().strip()

        if not all([state_number, model_text, color_text, owner_text]):
            messagebox.showwarning("Поля", "Заполните все поля")
            return

        try:
            model_name = model_text.split(" (")[0]
            brand_name = model_text.split(" (")[1][:-1]
            last_name, first_name = owner_text.split(" ")
        except Exception:
            messagebox.showerror("Ошибка", "Неверный формат модели или владельца")
            return

        data = {
            "model_name": model_name,
            "brand_name": brand_name,
            "color_name": color_text,
            "owner_last_name": last_name,
            "owner_first_name": first_name,
            "user": self.username,
            "version": self.selected_version,
        }

        try:
            response = requests.put(f"{API_URL}/vehicles/{self.selected_id}", json=data, timeout=3)
            if response.status_code == 200:
                messagebox.showinfo("Успех", "ТС обновлено")
                self.load_vehicles()
                self.unlock_entity()
                self.clear_form()
            elif response.status_code == 404:
                messagebox.showerror("Ошибка", "ТС не найдено")
            elif response.status_code == 422:
                messagebox.showerror(
                    "Ошибка валидации",
                    str(response.json().get("detail", "Некорректные данные")),
                )
            elif response.status_code == 409:
                messagebox.showerror(
                    "Блокировка",
                    "ТС редактируется другим пользователем. Сохранение невозможно.",
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось обновить ТС: {response.status_code} "
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при обновлении)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def delete_vehicle(self):
        if not self.selected_id:
            messagebox.showwarning("Выбор", "Выберите ТС для удаления")
            return

        confirm = messagebox.askyesno(
            "Подтверждение", f"Удалить ТС {self.selected_id}?"
        )
        if not confirm:
            return

        try:
            response = requests.delete(
                f"{API_URL}/vehicles/{self.selected_id}?user={self.username}", timeout=3
            )
            if response.status_code == 200:
                messagebox.showinfo("Успех", "ТС удалено")
                self.load_vehicles()
                self.unlock_entity()
                self.clear_form()
            
            elif response.status_code == 400:
                error_msg = response.json().get("detail", "Ошибка запроса")
                messagebox.showerror("Ошибка", f"Не удалось удалить ТС: {error_msg}")    
            elif response.status_code == 403:
                messagebox.showerror("Ошибка", "Недостаточно прав для удаления")
            elif response.status_code == 404:
                messagebox.showerror("Ошибка", "ТС не найдено")
            elif response.status_code == 409:
                messagebox.showerror(
                    "Блокировка",
                    "ТС редактируется другим пользователем. Удаление невозможно.",
                )
            else:
                messagebox.showerror(
                    "Ошибка", f"Не удалось удалить ТС: {response.status_code}"
                )
        except Timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут при удалении нарушения)")
        except ConnectionError:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {e}")

    def clear_form(self):
        self.unlock_entity()
        self.selected_id = None
        self.selected_version = None
        self.state_entry.delete(0, tk.END)
        self.model_cb.set("")
        self.color_cb.set("")
        self.owner_cb.set("")


    def refresh_data(self):
        self.load_vehicles()