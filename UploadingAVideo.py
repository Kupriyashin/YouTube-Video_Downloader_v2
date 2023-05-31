import shutil
import traceback
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from loguru import logger
import moviepy.editor as movie
import re


class UploadingAVideo(QObject):
    _signal_error = pyqtSignal(str)  # для ошибок
    _signal_all_finished = pyqtSignal(str)  # при конце работы
    _signal_progress_downloaded = pyqtSignal(str)
    _signal_video_and_audio_download_success = pyqtSignal()

    def __init__(self, path_saved=None, youtube_object=None, audio_object=None, video_object=None, name_video=None):
        super(UploadingAVideo, self).__init__()

        self.finish_video = None
        self.video = None
        self.audio = None
        self.video_path_saved = None
        self.audio_path_saved = None
        self.name_video = name_video
        self.path_saved = Path(path_saved)
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

        try:
            logger.info("Поток работает")
            logger.info(f"path_saved: {self.path_saved}")
            logger.info(f"youTube_object: {self.youTube_object}")
            logger.info(f"audio_object: {self.audio_object}")
            logger.info(f"video_object: {self.video_object}")
            logger.info(f"name_video: {self.name_video}")

            regular_expression = r"[^а-яА-ЯёЁa-zA-Z0-9 ]"
            self.name_video = re.sub(regular_expression, '', str(self.name_video))
            logger.info(f"Имя с очисткой от ненужных символов: {self.name_video}")

            self.video_path_saved = Path(self.path_saved / "video")
            self.audio_path_saved = Path(self.path_saved / "audio")

            logger.info(f"Пусть скачивания аудио: {self.audio_path_saved}")
            logger.info(f"Пусть скачивания видео: {self.video_path_saved}")

            self.audio_object[-1].download(self.audio_path_saved)
            self._signal_progress_downloaded.emit("Аудиофайл скачан!")
            logger.info(f"Аудиофайл скачан!")

            self.video_object[-1].download(self.video_path_saved)
            self._signal_progress_downloaded.emit("Видеофайл скачан!")
            logger.info(f"Видеофайл скачан!")

            self._signal_video_and_audio_download_success.emit()

            self._signal_progress_downloaded.emit("Объединяю файлы аудио и видео в один")

            self.video = movie.VideoFileClip(f"{Path(self.video_path_saved/self.name_video)}.webm")
            self.audio = movie.AudioFileClip(f"{Path(self.audio_path_saved/self.name_video)}.webm")
            self.finish_video = self.video.set_audio(self.audio)
            self.finish_video.write_videofile(f"{Path(self.path_saved/self.name_video)}.webm", logger=None)

            self._signal_progress_downloaded.emit("Удаляю остаточные файлы")

            shutil.rmtree(self.video_path_saved)
            shutil.rmtree(self.audio_path_saved)

            self._signal_progress_downloaded.emit("Очистка окончена! Видео скачано")

        except Exception:
            logger.error(traceback.format_exc())
            self._signal_error.emit("Ошибка загрузки видео, повторите попытку!")
            self._signal_all_finished.emit(" ")
            logger.info(f"Сработал блок ошибки")
        finally:
            self._signal_all_finished.emit("Загрузка завершена")
            logger.info(f"Сработал блок финали")
            self.video.close()
            self.audio.close()
            self.finish_video.close()
