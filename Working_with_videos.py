from datetime import timedelta

import httplib2
from loguru import logger
from PyQt5.QtCore import pyqtSignal, QObject
from pytube import YouTube
from PIL import Image


class WorkingWithVideos(QObject):
    """
    Класс потока для получения информации о видео и его загрузки в отдельном потоке.
     Получаемая информации:
    - титульное изображение
    - описание видео
    - автор видео
    - название видео
    - ключевые слова
    - количество просмотров
    - длина видео в секундах
    """

    _signal_information_text_true = pyqtSignal(str)
    _signal_error = pyqtSignal(str)  # сигнал об ошибке
    _signal_streams_true = pyqtSignal(str)  # сигнал о получении стримов видео
    _signal_progress = pyqtSignal(int)  # сигнал о прогрессе получения информации

    # Сигналы для метода get_information
    _signal_author = pyqtSignal(str)
    _signal_title = pyqtSignal(str)
    _signal_keywords_video = pyqtSignal(str)
    _signal_views = pyqtSignal(str)
    _signal_length = pyqtSignal(str)
    _signal_description = pyqtSignal(str)
    _signal_title_image = pyqtSignal(str)
    _completely_finished_the_work = pyqtSignal(dict)

    def __init__(self, url: str, progress):
        super(WorkingWithVideos, self).__init__()
        self.__youtube_object = None
        self.__youtube_streams = None
        self.url_video = url
        self.progress_download = progress

    def get_information(self):
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
                    self.__youtube_streams = self.__youtube_object.streams

                    if self.__youtube_streams:
                        self._signal_streams_true.emit("Стримы видео получены успешно")

                        break
                except Exception:
                    self._signal_error.emit("Ошибка при получении стримов видео")

            logger.info(f"Получен объект youtube: {self.__youtube_object}, его тип: {type(self.__youtube_object)}")
            logger.info(f"Получен объект streams: {self.__youtube_streams}, его тип: {type(self.__youtube_streams)}")

            self._signal_progress.emit(0)
            """Автор видео"""
            try:
                self._signal_author.emit(str(self.__youtube_object.author))
                self._signal_progress.emit(int(100 / 7))
                self._signal_information_text_true.emit("Автор видео найден")

            except Exception:
                self._signal_error.emit("Ошибка получения автора видео")

            """Название видео"""
            try:
                self._signal_title.emit(str(self.__youtube_object.title))
                self._signal_progress.emit(int(100 / 6))
                self._signal_information_text_true.emit("Название видео найдено")

            except Exception:
                self._signal_error.emit("Ошибка получения названия видео")

            """Ключевые слова видео"""
            try:
                _keyword = ", ".join(self.__youtube_object.keywords)
                self._signal_keywords_video.emit(str(_keyword))
                self._signal_progress.emit(int(100 / 5))
                self._signal_information_text_true.emit("Ключевые слова получены")

            except Exception:
                self._signal_error.emit("Ошибка получения ключевых слов видео")

            """Количество просмотров видео"""
            try:
                self._signal_views.emit(str(self.__youtube_object.views))
                self._signal_progress.emit(int(100 / 4))
                self._signal_information_text_true.emit("Количество просмотров получено")

            except Exception:
                self._signal_error.emit("Ошибка получения просмотров видео")

            """Длина видео"""
            try:
                self._signal_length.emit(str(timedelta(seconds=self.__youtube_object.length)))
                self._signal_progress.emit(int(100 / 3))
                self._signal_information_text_true.emit("Длина видео получена")

            except Exception:
                self._signal_error.emit("Ошибка при получении длины видео")

            """Описание видео"""
            try:

                self._signal_description.emit(str(self.__youtube_object.description))
                self._signal_progress.emit(int(100 / 2))
                self._signal_information_text_true.emit("Описание видео получено")

            except Exception:
                self._signal_error.emit("Ошибка при получении описания видео")

            """Титульное изображение видео"""
            try:
                self._thumbnail_url = self.__youtube_object.thumbnail_url  # ссылка на титульное изображение

                self._http_downloader = httplib2.Http('.cache')
                _, content = self._http_downloader.request(self._thumbnail_url)

                # logger.info(f"content: {content.decode('utf')}")

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

    def dowload_video_and_audio(self):
        pass
