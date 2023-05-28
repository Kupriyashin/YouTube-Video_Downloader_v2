import random
import time
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal
from loguru import logger


class VisualizationStub(QObject):
    _signal_random_value = pyqtSignal(int)
    _signal_finished = pyqtSignal()
    _signal_random_data = pyqtSignal(str)

    def __init__(self, parent_window=None):
        super(VisualizationStub, self).__init__()
        self.value_stop_work = None
        self.parent_window = parent_window
        self.parent_window.signal_stop_random.connect(lambda val: self.stop_work(val))

    def visualization_stub_func(self):
        logger.info("Поток работает")
        while self.value_stop_work is None:
            logger.info(f"Функция рандомной визуализации работает, {datetime.now().strftime('%H:%M:%S')}")

            self._signal_random_value.emit(random.randint(1, 99))
            self._signal_random_data.emit(str(f"Обработано данных: {random.randint(1, 1_048_576 / 2)} байт"))

            time.sleep(random.random())

            if self.value_stop_work is not None:
                self._signal_finished.emit()
                logger.info("Файл скачан")
                break
        logger.info("Бесконечный цикл успешно закончен")

    def stop_work(self, value):
        self.value_stop_work = value
