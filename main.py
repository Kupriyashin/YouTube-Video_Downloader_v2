from loguru import logger
from pytube import YouTube
import tkinter as base_tk
import customtkinter as cum_tk
from datetime import datetime


def geometry_center():
    window_height = 500
    window_width = 900

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))

    root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))


logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")
cum_tk.set_appearance_mode("System")
cum_tk.set_default_color_theme("green")
root = cum_tk.CTk()
root.title("Video YouTube Downloader")
root.wm_iconbitmap(default="Resources/ICO Youtube downloader.ico")
geometry_center()


def button_function():
    print("button pressed")


# Use CTkButton instead of tkinter Button
button = cum_tk.CTkButton(master=root, text="CTkButton", command=button_function)
button.place(relx=0.5, rely=0.5, anchor=base_tk.CENTER)

if __name__ == '__main__':
    root.mainloop()

"""def list_add_item(self, text: str, true_false: bool):
    try:

        if true_false:
            self.ui.listWidget.addItem(f"✅{datetime.now().strftime('%H:%M:%S')} - {text}")
            self.ui.listWidget.scrollToBottom()

        else:
            self.ui.listWidget.addItem(f"❌{datetime.now().strftime('%H:%M:%S')} - {text}")
            self.ui.listWidget.scrollToBottom()

    except Exception:

        self.ui.listWidget.addItem(
            f"❌{datetime.now().strftime('%H:%M:%S')} - Произошла внутренняя ошибка обмена данными")
        self.ui.listWidget.addItem(
            f"❌{datetime.now().strftime('%H:%M:%S')} - ❌ПЕРЕЗАГРУЗИТЕ ПРИЛОЖЕНИЕ!❌")
        self.ui.listWidget.scrollToBottom()"""
