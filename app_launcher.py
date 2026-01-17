import tkinter as tk
from tkinter import messagebox
import requests
from gui_main import launch_main  # 👈 GUI-файл теперь только с launch_main()

API_URL = "http://localhost:8000"


def login_window():
    login = tk.Tk()
    login.title("🔐 Вход в систему")
    login.geometry("300x150")

    # Центрирование окна
    login.update_idletasks()
    w = login.winfo_screenwidth()
    h = login.winfo_screenheight()
    size = tuple(int(_) for _ in login.geometry().split("+")[0].split("x"))
    x = w // 2 - size[0] // 2
    y = h // 2 - size[1] // 2
    login.geometry(f"{size[0]}x{size[1]}+{x}+{y}")

    # Поля ввода
    tk.Label(login, text="Имя пользователя:", font=("Segoe UI", 10)).pack(pady=10)
    username_entry = tk.Entry(login, font=("Segoe UI", 10))
    username_entry.pack(pady=5)

    def submit():
        username = username_entry.get().strip()
        if not username:
            messagebox.showwarning("Ошибка", "Введите имя пользователя")
            return
        try:
            response = requests.post(
                f"{API_URL}/auth/login", json={"username": username}, timeout=3
            )
            if response.status_code == 200:
                role = response.json()["role"]
                login.destroy()
                launch_main(username, role)
            elif response.status_code == 404:
                messagebox.showerror("Ошибка", "Пользователь не найден")
            else:
                messagebox.showerror(
                    "Ошибка", f"Ошибка авторизации: {response.status_code}"
                )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Сервер недоступен: {e}")

    tk.Button(login, text="Войти", command=submit).pack(pady=10)
    login.mainloop()


if __name__ == "__main__":
    login_window()
