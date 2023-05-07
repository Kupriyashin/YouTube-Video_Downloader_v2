from pprint import pprint
import re

from PyQt5.QtGui import QIcon
from loguru import logger
from pytube import YouTube
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets
import sys
from Form import Ui_MainWindow

"""
Компиляция приложения в виде установщика - https://pythonist.ru/rukovodstvo-po-pyqt5/
"""
logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    __url_video = None
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Video YouTube Downloader")
        self.setWindowIcon(QIcon("Resources/folderreddownload_93315.ico"))

        self.ui.comboBox.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)

        self.ui.pushButton.clicked.connect(self.getting_information_about_the_video)

    def getting_information_about_the_video(self):
        if re.fullmatch(r"^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+", self.ui.lineEdit.text()):

            self.logging_of_information(text="Указана верная ссылка на видео", true_false=True)

            self.__url_video = self.ui.lineEdit.text()

            self.ui.lineEdit.setEnabled(False)
            self.ui.pushButton.setEnabled(False)
            logger.info(f"Ссылка на видео: {self.__url_video}")
        else:
            self.logging_of_information(text="Указана неверная ссылка на видео", true_false=False)

    def logging_of_information(self, text: str, true_false: bool):
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
            self.ui.listWidget.scrollToBottom()


if __name__ == '__main__':
    _app = QApplication(sys.argv)
    _window = MainWindow()
    _window.show()
    sys.exit(_app.exec_())


