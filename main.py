import os
import traceback
import re
import httplib2
from PyQt5.QtGui import QIcon, QPixmap
from loguru import logger
from pytube import YouTube
from datetime import datetime
from datetime import timedelta
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets
import sys
from Form import Ui_MainWindow
from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image

"""
Компиляция приложения в виде установщика - https://pythonist.ru/rukovodstvo-po-pyqt5/

Преобразование uic -> py: pyuic5 Form/form_downloader.ui -o Form/Form_downloader.py

Как удалить commit в Github:
1. Получаем хэш-код коммита, к которому хотим вернуться.
2. Заходим в папку репозитория и пишем в консоль:
    $ git reset --hard <хэш-код коммита> 
    $ git push --force
    
создание requirements файла: pip3 freeze > requirements.txt
"""

logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()

        self.__url_video = None
        self.__YouTube_object = None
        self.__streams = None

        self._thread_video_information = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Video YouTube Downloader")
        self.setWindowIcon(QIcon("Resources/folderreddownload_93315.ico"))

        self.ui.comboBox.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)

        self.ui.label.setPixmap(QPixmap(r"Title Image/error_image.jpg"))

        self.ui.listWidget.setWordWrap(True)
        self.ui.textEdit.setReadOnly(True)
        self.ui.textEdit.setText("Нет информации")

        self.ui.pushButton.clicked.connect(self.getting_information_about_the_video)

    @logger.catch()
    def download_progress(self, chunk, file_handle, bytes_remaining):
        logger.info(f"chunk: {chunk}")
        logger.info(f"file_handle: {file_handle}")
        logger.info(f"bytes_remaining: {bytes_remaining}")

    @logger.catch()
    def logging_of_information(self, text: str, true_false: bool):
        """
        визуализация действий программы в listWidget'е для логирования
        :param text:
        :param true_false:
        :return:
        """
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

    def getting_information_about_the_video(self):
        """
        Функция-обработчик кнопки получения информации о видео.
        Срабатывает при нажатии кнопки и проверяет: соответствует ли введенный текст в ListWidget регулярному выражению
        :return:
        """
        if re.fullmatch(r"^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+", self.ui.lineEdit.text()):

            self.logging_of_information(text="Указана верная ссылка на видео", true_false=True)

            self.__url_video = self.ui.lineEdit.text()

            self.ui.lineEdit.setEnabled(False)
            self.ui.pushButton.setEnabled(False)

            logger.info(f"Ссылка на видео: {self.__url_video}")

            self.getting_information_in_a_separate_stream()

        else:
            self.logging_of_information(text="Указана неверная ссылка на видео", true_false=False)

    @logger.catch()
    def getting_information_in_a_separate_stream(self):
        """
        Запускается отдельный поток для получения информации о видео в классе - StreamToGetInformationAboutTheVideo
        :return:
        """
        try:
            self._thread_video_information = StreamToGetInformationAboutTheVideo(url=self.__url_video,
                                                                                 progress=self.download_progress)

            # начало потока
            self._thread_video_information.started.connect(
                lambda: self.logging_of_information(text="Начал получать инфомрацию о видео", true_false=True))

            self._thread_video_information.started.connect(
                lambda: self.ui.progressBar.setValue(0))

            # рабочие сигналы
            self._thread_video_information._signal_error.connect(
                lambda text: self.logging_of_information(text=text, true_false=False))

            self._thread_video_information._signal_streams_true.connect(
                lambda text: self.logging_of_information(text=text, true_false=True))

            self._thread_video_information._signal_progress.connect(lambda num: self.ui.progressBar.setValue(num))

            self._thread_video_information._signal_author.connect(
                lambda text: self.author_add(text))

            self._thread_video_information._signal_information_text_true.connect(
                lambda text: self.logging_of_information(text=text, true_false=True))

            self._thread_video_information._signal_title.connect(lambda text: self.title_add(text))

            self._thread_video_information._signal_keywords_video.connect(lambda text: self.keywords_add(text))

            self._thread_video_information._signal_views.connect(lambda text: self.views_add(text))

            self._thread_video_information._signal_length.connect(lambda text: self.length_add(text))

            self._thread_video_information._signal_description.connect(lambda text: self.description_add(text))

            self._thread_video_information._signal_title_image.connect(lambda text: self.image_title_add(text))

            self._thread_video_information._completely_finished_the_work.connect(
                lambda objects: self.working_with_youtube_objects(objects))

            # конец потока
            self._thread_video_information.finished.connect(
                lambda: self.logging_of_information(text="Получение информации окончено", true_false=True))

            self._thread_video_information.finished.connect(
                lambda: self.ui.progressBar.setValue(100))

            # запуск потока
            self._thread_video_information.start()

        except Exception:
            logger.error(traceback.format_exc())
            self.logging_of_information(text="Ошибка в получении информации о видео", true_false=False)

            self.ui.lineEdit.setEnabled(True)
            self.ui.pushButton.setEnabled(True)

    @logger.catch()
    def working_with_youtube_objects(self, objects: dict):
        try:
            self.__YouTube_object = objects.get("object_youtube")
            self.__streams = objects.get("stream_object")

            logger.info(f"object_youtube: {self.__YouTube_object}")
            logger.info(f"stream_object: {self.__streams}")

        except Exception:
            self.logging_of_information(text="❌❌❌Критическая ошибка! Повторите загрузку!❌❌❌", true_false=False)

            self.ui.label.setPixmap(QPixmap("Title Image/error_image.jpg"))

            self.ui.textEdit.clear()
            self.ui.textEdit.setText("Нет информации")

            self.ui.lineEdit.setEnabled(True)
            self.ui.pushButton.setEnabled(True)

            self.ui.label_4.setText("Нет информации")
            self.ui.label_4.setStyleSheet("color: red;")
            self.ui.label_6.setText("Нет информации")
            self.ui.label_6.setStyleSheet("color: red;")
            self.ui.label_10.setText("Нет информации")
            self.ui.label_10.setStyleSheet("color: red;")
            self.ui.label_12.setText("Нет информации")
            self.ui.label_12.setStyleSheet("color: red;")
            self.ui.label_15.setText("Нет информации")
            self.ui.label_15.setStyleSheet("color: red;")

    @logger.catch()
    def image_title_add(self, path: str):
        try:
            self.ui.label.setPixmap(QPixmap(path))
            os.remove(path)

        except Exception:
            self.logging_of_information(text="Ошибка при получении титульного изображения видео", true_false=False)

    @logger.catch()
    def description_add(self, description: str):
        try:
            self.ui.textEdit.clear()
            self.ui.textEdit.setText(description)
            logger.info(f"Описание видо: {description}")

        except Exception:
            self.logging_of_information(text="Ошибка при получении описания видео", true_false=False)

    @logger.catch()
    def length_add(self, length: str):
        try:
            self.ui.label_15.setText(length)
            self.ui.label_15.setStyleSheet("color: green;")

            logger.info(f"Длина видео: {length}")
        except Exception:
            self.logging_of_information(text="Ошибка при получении длины видео", true_false=False)

    @logger.catch()
    def views_add(self, views: str):
        try:
            self.ui.label_12.setText("{0:,}".format(int(views)).replace(",", " "))
            self.ui.label_12.setStyleSheet("color: green;")

            logger.info(f"Количество просмотров: {views}")
        except Exception:
            self.logging_of_information(text="Ошибка при получении количества просмотров видео", true_false=False)

    @logger.catch()
    def keywords_add(self, keywords: str):
        try:
            _length_symbol = 71
            _words = ''

            if len(keywords.lower()) > _length_symbol:
                _words = ''.join(keywords[:71]) + " ..."
            else:
                _words = keywords

            self.ui.label_10.setText(_words)
            self.ui.label_10.setStyleSheet("color: green;")

            logger.info(f"Ключевые слова видео: {_words}")
        except Exception:
            self.logging_of_information(text="Ошибка при получении ключевых слов видео", true_false=False)

    @logger.catch()
    def title_add(self, title: str):
        try:
            _length_symbol = 71
            _words = ''
            if len(title.lower()) > _length_symbol:
                _words = ''.join(title.lower()[:71]) + " ..."
            else:
                _words = title

            self.ui.label_6.setText(_words.capitalize())
            self.ui.label_6.setStyleSheet("color: green;")

            logger.info(f"Название видео: {_words}")
        except Exception:
            self.logging_of_information(text="Ошибка при получении названия видео", true_false=False)

    @logger.catch()
    def author_add(self, author: str):
        try:
            self.ui.label_4.setText(author)
            self.ui.label_4.setStyleSheet("color: green;")
            logger.info(f"Автор видео: {author}")
        except Exception:
            self.logging_of_information(text="Ошибка при получении автора видео", true_false=False)


class StreamToGetInformationAboutTheVideo(QThread):
    """
    Класс потока для получения информации о видео. Получаемая информации:
    - титульное изображение
    - описание видео
    - автор видео
    - название видео
    - ключевые слова
    - количество просмотров
    - длина видео в секундах
    """

    _signal_information_text_true = pyqtSignal(str)
    _signal_error = pyqtSignal(str)  # сигнал о ошибка
    _signal_streams_true = pyqtSignal(str)  # сигнал о получении стримов видео
    _signal_progress = pyqtSignal(int)  # сигнал о прогрессе получения информации

    _signal_author = pyqtSignal(str)
    _signal_title = pyqtSignal(str)
    _signal_keywords_video = pyqtSignal(str)
    _signal_views = pyqtSignal(str)
    _signal_length = pyqtSignal(str)
    _signal_description = pyqtSignal(str)
    _signal_title_image = pyqtSignal(str)
    _completely_finished_the_work = pyqtSignal(dict)

    def __init__(self, url: str, progress, parent=None):
        QThread.__init__(self, parent)
        self.__youtube_object = None
        self.__youtube_streams = None
        self.url_video = url
        self.progress_download = progress

    def run(self):
        """
        Чтобы не возникало ошибок при загрузке стримов видео необходимо в файле
         "...venv\Lib\site-packages\pytube\innertube.py" в 78 строке поменять client='ANDROID' на client='WEB'
        :return:
        """
        try:
            for _ in range(5):
                try:
                    self._signal_progress.emit(_ * 100 / 5)

                    self.__youtube_object = YouTube(self.url_video, on_progress_callback=self.progress_download)
                    self.__youtube_streams = self.__youtube_object.streams.all()

                    if self.__youtube_streams:
                        self._signal_streams_true.emit("Стримы видео получены успешно")

                        self.__youtube_streams = list(enumerate(self.__youtube_streams))

                        break
                except Exception:
                    self._signal_error.emit("Ошибка при получении стримов видео")

            logger.info(f"Получен объект youtube: {self.__youtube_object}, его тип: {type(self.__youtube_object)}")
            logger.info(f"Получен объект streams: {self.__youtube_streams}, его тип: {type(self.__youtube_streams)}")

            self._signal_progress.emit(0)
            # Автор видео
            try:
                self._signal_author.emit(str(self.__youtube_object.author))
                self._signal_progress.emit(int(100 / 7))
                self._signal_information_text_true.emit("Автор видео найден")

            except Exception:
                self._signal_error.emit("Ошибка получения автора видео")

            # Название видео
            try:
                self._signal_title.emit(str(self.__youtube_object.title))
                self._signal_progress.emit(int(100 / 6))
                self._signal_information_text_true.emit("Название видео найдено")

            except Exception:
                self._signal_error.emit("Ошибка получения названия видео")

            # Ключевые слова видео
            try:
                _keyword = ", ".join(self.__youtube_object.keywords)
                self._signal_keywords_video.emit(str(_keyword))
                self._signal_progress.emit(int(100 / 5))
                self._signal_information_text_true.emit("Ключевые слова получены")

            except Exception:
                self._signal_error.emit("Ошибка получения ключевых слов видео")

            # Количество просмотров видео
            try:
                self._signal_views.emit(str(self.__youtube_object.views))
                self._signal_progress.emit(int(100 / 4))
                self._signal_information_text_true.emit("Количество просмотров получено")

            except Exception:
                self._signal_error.emit("Ошибка получения просмотров видео")

            # Длина видео
            try:
                self._signal_length.emit(str(timedelta(seconds=self.__youtube_object.length)))
                self._signal_progress.emit(int(100 / 3))
                self._signal_information_text_true.emit("Длина видео получена")

            except Exception:
                self._signal_error.emit("Ошибка при получении длины видео")

            # Описание видео
            try:

                self._signal_description.emit(str(self.__youtube_object.description))
                self._signal_progress.emit(int(100 / 2))
                self._signal_information_text_true.emit("Описание видео получено")

            except Exception:
                self._signal_error.emit("Ошибка при получении описания видео")

            # Титульное изображение видео
            try:
                self._thumbnail_url = self.__youtube_object.thumbnail_url  # ссылка на титульное изображение

                self._http_downloader = httplib2.Http('.cache')
                _, content = self._http_downloader.request(self._thumbnail_url)

                with open("Title Image/working_image.jpg", "wb") as image_file:
                    image_file.write(content)

                Image.open("Title Image/working_image.jpg").resize((250, 150)).save(
                    "Title Image/working_image.jpg")

                self._signal_title_image.emit("Title Image/working_image.jpg")
                self._signal_progress.emit(int(100 / 1))
                self._signal_information_text_true.emit("Титульное изображение видео получено")

            except Exception:
                self._signal_error.emit("Ошибка при получении титульного изображения видео")

            self._completely_finished_the_work.emit(
                {"object_youtube": self.__youtube_object, "stream_object": self.__youtube_streams})

        except Exception:
            self._signal_error.emit("Ошибка при получении информации о видео")


if __name__ == '__main__':
    _app = QApplication(sys.argv)
    _app.setStyle("Fusion")
    _window = MainWindow()
    _window.show()
    sys.exit(_app.exec_())
