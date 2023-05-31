import os
import traceback
import re

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from loguru import logger
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5 import QtWidgets
import sys

from Form import Ui_MainWindow
from WorkingWithVideos import WorkingWithVideos
from UploadingAVideo import UploadingAVideo
from KitajskyKostil import VisualizationStub

"""
Лучше сделать еще один файл с классом под еще 1 поток!
При первом вызове потока лучше явно вызывать выход из него (то есть испускать из него сигнал и по данному сигналу его закрывать)
А то че то он когда хочет закрывается, как то странно
"""

"""
Компиляция приложения в виде установщика - https://habr.com/ru/companies/vdsina/articles/557316/

Преобразование uic -> py: pyuic5 Form/form_downloader.ui -o Form/Form_downloader.py

Как удалить commit в Github:
1. Получаем хэш-код коммита, к которому хотим вернуться.
2. Заходим в папку репозитория и пишем в консоль:
    $ git reset --hard <хэш-код коммита> 
    $ git push --force
    
создание requirements файла: pip3 freeze > requirements.txt

Манал я эту библиотеку pytube: как оказалось она не способна параллельно давать количество скачанного и скачивать видео (либо у меня руки кривые либо это действительно так),
ввиду чего было придумано решение сделать "Китайский костыль" - это, выполняемый цикл в отдельном потоке для передачи рандомного значения для прогресс бара.
Ввиду того, что при скачивании программа, хоть и не умерает, но и ничего не делает, следовательно посльзователь может ее просто вырубить, подлумав, что она зависла.
Соответственно, подстановка рандомного значения в прогресс бар может частично решить данную проблему.
"""

logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    _signal_stop_random = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self._name_video = None
        self._working_with_videos_class = None
        self._additional_stream_class = None
        self._download_video_class_thread = None
        self._stream = None
        self._progressive_false = None
        self._video = None
        self._audio = None

        self.__url_video = None
        self.__YouTube_object = None
        self.__streams = None
        self.__path_saved = None

        self._thread_video_information = None

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Video YouTube Downloader")
        self.setWindowIcon(QIcon("Resources/folderreddownload_93315.ico"))

        self.ui.label.setPixmap(QPixmap(r"Title Image/error_image.jpg"))

        self.ui.listWidget.setWordWrap(True)
        self.ui.textEdit.setReadOnly(True)
        self.ui.textEdit.setText("Нет информации")

        self.ui.pushButton.clicked.connect(self.getting_information_about_the_video)
        self.ui.pushButton_3.clicked.connect(lambda: self.path_saved_video())
        self.ui.pushButton_2.clicked.connect(lambda: self.video_and_audio_download())

        self.ui.comboBox.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)

    @logger.catch()
    def video_and_audio_download(self):
        try:
            self.ui.pushButton_2.setEnabled(False)
            self._stream = self.ui.comboBox.currentText().split(': ')[-1]
            logger.info(self._stream)

            for item in self.__streams:
                if self._stream in str(item[-1]):
                    self.__streams = item
                    break

            logger.info("__________________Основные передаваемые объекты для скачивания__________________")
            logger.info(f"Объект пути сохранения: {self.__path_saved}")  # пусть
            logger.info(f"Объект Ютуба: {self.__YouTube_object}")  # объект ютуба
            logger.info(f"Объект аудио: {self._audio}")  # аудио стрим
            logger.info(f"Объект видео: {self.__streams}")  # видео стрим
            logger.info(f"Название видео: {self._name_video}")

            logger.info(f"Тип данных пути: {type(self.__path_saved)}")  # тип данных пусть
            logger.info(f"Тип данных объекта ютуб: {type(self.__YouTube_object)}")  # тип данных объект ютуба
            logger.info(f"Тип данных аудио: {type(self._audio)}")  # тип данных аудио стрим
            logger.info(f"Тип данных видео: {type(self.__streams)}")  # тип данных видео стрим

            # ___________________________________________Скачивание видео в другом потоке___________________________________________

            # создание экземпляра класса загрузки видео с нужными параметрами
            self._download_class = UploadingAVideo(path_saved=self.__path_saved, youtube_object=self.__YouTube_object,
                                                   audio_object=self._audio, video_object=self.__streams,
                                                   name_video=self._name_video)

            # класс дополнительного потока и помещения объекта в поток
            self._download_new_thread = QThread()  # поток
            self._download_class.moveToThread(self._download_new_thread)

            # начало потока
            self._download_new_thread.started.connect(self._download_class.uploading_a_video)
            self._download_new_thread.started.connect(lambda: self.ui.progressBar.setValue(0))

            self._download_new_thread.started.connect(
                lambda: self.logging_of_information(text="Начал загрузку видео", true_false=True)
            )

            # рабочие сигналы
            self._download_class._signal_error.connect(
                lambda text: self.logging_of_information(text=text, true_false=False))

            self._download_class._signal_error.connect(
                lambda: self.finished_download_video())

            self._download_class._signal_progress_downloaded.connect(lambda text: self.logging_of_information(text=text, true_false=True))

            # конец потока
            self._download_class._signal_all_finished.connect(self._download_new_thread.quit)

            self._download_new_thread.finished.connect(
                lambda: self.logging_of_information(text="Download completed successfully!😎", true_false=True))

            self._download_new_thread.finished.connect(lambda: self.ui.progressBar.setValue(100))

            self._download_new_thread.finished.connect(lambda: self.finished_download_video())
            self._download_new_thread.finished.connect(lambda: self._signal_stop_random.emit(1))

            # запуск потока
            self._download_new_thread.start()

            # ___________________________________________Конец скачивание видео в другом потоке___________________________________________

            # _____________________________________Заглушка для визуализации скачивнаия в другом потоке___________________________________

            self._stub_visualization_stream = QThread()
            self._visualization_stub_class = VisualizationStub(parent_window=self)

            # закидываем выполнение в другой поток
            self._visualization_stub_class.moveToThread(self._stub_visualization_stream)

            # старт потока
            self._stub_visualization_stream.started.connect(self._visualization_stub_class.visualization_stub_func)

            # рабочие сигналы
            self._visualization_stub_class._signal_random_value.connect(lambda val: self.ui.progressBar.setValue(val))

            self._visualization_stub_class._signal_random_data.connect(
                lambda text: self.logging_of_information(text=text, true_false=True))

            # конец потока
            self._visualization_stub_class._signal_finished.connect(self._stub_visualization_stream.quit)

            # Запуск потока
            self._stub_visualization_stream.start()


        except Exception:

            self.logging_of_information(text="❌❌❌Критическая ошибка! Повторите загрузку!❌❌❌", true_false=False)
            logger.error(traceback.format_exc())

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
            self.ui.comboBox.clear()

    @logger.catch()
    def path_saved_video(self):
        try:
            _path_directory = QFileDialog.getExistingDirectory(self, 'Выберите папку для сохранения видео')

            if _path_directory:
                self.__path_saved = _path_directory

                self.logging_of_information(text=f"Папка сохранения файла: {self.__path_saved}", true_false=True)
                self.logging_of_information(text=f"ВЫ МОЖЕТЕ СКАЧАТЬ ВИДЕО В ВЫБРАННОМ КАЧЕСТВЕ", true_false=True)
                logger.info(f"Путь сохранения видео: {self.__path_saved}")

                self.ui.comboBox.setEnabled(False)
                self.ui.pushButton_3.setEnabled(False)
                self.ui.pushButton_2.setEnabled(True)

            else:

                self.logging_of_information(text="Папка сохранения не выбрана", true_false=False)

        except Exception:

            self.logging_of_information(text="❌❌❌Критическая ошибка! Повторите загрузку!❌❌❌", true_false=False)
            logger.error(traceback.format_exc())

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
            self.ui.comboBox.clear()

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
        Запускается отдельный поток для получения информации о видео в классе - WorkingWithVideos (from Working_with_videos import WorkingWithVideos)
        :return:
        """
        try:
            # объект класса для получения информации и скачивания видео
            self._thread_video_information = WorkingWithVideos(url=self.__url_video)

            # класс дополнительного потока и помещения объекта в поток
            self._additional_stream_class = QThread()
            self._thread_video_information.moveToThread(self._additional_stream_class)

            # начало потока
            self._additional_stream_class.started.connect(self._thread_video_information.get_information)

            self._additional_stream_class.started.connect(
                lambda: self.logging_of_information(text="Начал получать инфомрацию о видео", true_false=True))

            self._additional_stream_class.started.connect(
                lambda: self.ui.progressBar.setValue(0))

            # рабочие сигналы
            self._thread_video_information._signal_error.connect(
                lambda text: self.logging_of_information(text=text, true_false=False))

            self._thread_video_information._signal_error_crit.connect(lambda: self.error_crit())

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

            self._thread_video_information._completely_finished_the_work.connect(self._additional_stream_class.quit)

            self._additional_stream_class.finished.connect(
                lambda: self.logging_of_information(text="Получение информации окончено", true_false=True))

            self._additional_stream_class.finished.connect(
                lambda: self.ui.progressBar.setValue(100))

            # запуск потока
            self._additional_stream_class.start()

        except Exception:
            logger.error(traceback.format_exc())
            self.logging_of_information(text="Ошибка в получении информации о видео", true_false=False)

            self.ui.lineEdit.setEnabled(True)
            self.ui.pushButton.setEnabled(True)

    @logger.catch()
    def error_crit(self):
        self.ui.pushButton.setEnabled(True)
        self.ui.lineEdit.setEnabled(True)

    @logger.catch()
    def working_with_youtube_objects(self, objects: dict):
        try:
            self.__YouTube_object = objects.get("object_youtube")
            self.__streams = list(enumerate(objects.get("stream_object")))

            logger.info(f"object_youtube: {self.__YouTube_object}")
            logger.info(f"stream_object: {self.__streams}")

            self._progressive_false = []
            self._video = []
            self._audio = []

            # получаю только стримы с раздельным видео и аудио
            for stream in self.__streams:
                if "False" in str(stream[1]):
                    self._progressive_false.append(stream)

            # получаю стримы только с видеокодеком vp9
            for video in self._progressive_false:
                if "vp9" in str(video[1]):
                    self._video.append(video)
                    item = str(video).split(' ')[2].split('"') + str(video).split(' ')[4].split('"')
                    item = f"{item[4]} - Тег: {item[1]}"
                    logger.info(f"Item в комбобокс: {item}")
                    self.ui.comboBox.addItem(item)
                    self.logging_of_information(text=f"Можно скачать {item}", true_false=True)

            # получаю аудио только с аудиокодеком opus
            for audio in self._progressive_false:
                if "opus" in str(audio[1]):
                    self._audio.append(audio)

            # беру самый тяжелый по скачиванию стрим аудио
            self._audio = self._audio[-1]

            self.ui.comboBox.setEnabled(True)
            if self.__path_saved:
                self.ui.pushButton_3.setEnabled(True)
                self.ui.pushButton_2.setEnabled(True)
            else:
                self.ui.pushButton_3.setEnabled(True)

            logger.info(self._progressive_false)
            logger.info(self._video)
            logger.info(self._audio)

        except Exception:
            self.logging_of_information(text="❌❌❌Критическая ошибка! Повторите загрузку!❌❌❌", true_false=False)
            logger.error(traceback.format_exc())

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

    # ___________________________ Методы для заполнения информации о видосе в полях ___________________________
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
            self._name_video = title
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

    # ___________________________ Выполняется после загрузки видео ___________________________
    @logger.catch()
    def finished_download_video(self):
        try:
            self.ui.comboBox.clear()
            self.ui.comboBox.setEnabled(False)
            self.ui.pushButton_3.setEnabled(False)

            self.ui.pushButton_2.setEnabled(False)

            self.ui.lineEdit.clear()
            self.ui.lineEdit.setEnabled(True)
            self.ui.pushButton.setEnabled(True)
        except Exception:
            logger.info(f"Ошибка в блоке finished_download_video")
            logger.error(traceback.format_exc())

    # ХЗ че это, само собой появилось, когда я в левом потоке объявил данный метод
    @property
    def signal_stop_random(self):
        return self._signal_stop_random


if __name__ == '__main__':
    _app = QApplication(sys.argv)
    _app.setStyle("Fusion")
    _window = MainWindow()
    _window.show()
    sys.exit(_app.exec_())
