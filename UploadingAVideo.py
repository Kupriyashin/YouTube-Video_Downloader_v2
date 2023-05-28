import traceback
from pytube.cli import on_progress

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from loguru import logger
import asyncio


class UploadingAVideo(QObject):
    _signal_error = pyqtSignal(str)  # для ошибок
    _signal_all_finished = pyqtSignal(str)  # при конце работы
    _signal_progress = pyqtSignal(int)

    def __init__(self, path_saved=None, youtube_object=None, audio_object=None, video_object=None, name_video=None):
        super(UploadingAVideo, self).__init__()

        self._file_size = None
        self.name_video = name_video
        self.path_saved = path_saved
        self.youTube_object = youtube_object
        self.audio_object = audio_object
        self.video_object = video_object

        self._stream = None
        self._chunk = None
        self._file_handle = None
        self._bytes_remaining = None

    @logger.catch()
    @pyqtSlot()
    def uploading_a_video(self):
        @logger.catch()
        @pyqtSlot()
        def process_downloading(chunk, file_handle, bytes_remaining):
            logger.info(f"chunk: {chunk}")
            logger.info(f"file_handle: {file_handle}")
            logger.info(f"bytes_remaining: {bytes_remaining}")

            progress = float(abs((bytes_remaining - self._file_size) / self._file_size)) * float(100)
            self._signal_progress.emit(int(progress))

        try:
            logger.info("Поток работает")
            logger.info(f"path_saved: {self.path_saved}")
            logger.info(f"youTube_object: {self.youTube_object}")
            logger.info(f"audio_object: {self.audio_object}")
            logger.info(f"video_object: {self.video_object}")
            logger.info(f"name_video: {self.name_video}")

            self._file_size = self.audio_object[-1].filesize
            logger.info(f"Размер аудио: {self._file_size} байт")

            self.youTube_object.register_on_progress_callback(on_progress)
            self.audio_object[-1].download(self.path_saved)
            logger.info(f"Аудиофайл скачан!")

        except Exception:
            logger.error(traceback.format_exc())
            self._signal_error.emit("Ошибка загрузки видео, повторите попытку!")
            self._signal_all_finished.emit(" ")
            logger.info(f"Сработал блок ошибки")
        finally:
            self._signal_all_finished.emit("Загрузка завершена")
            logger.info(f"Сработал блок финали")
