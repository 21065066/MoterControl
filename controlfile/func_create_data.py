from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QMutex
import random
import json
from random import randint
import time

class UpdateDataThread(QThread):
    _signal_update = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.qmut = QMutex()
        self.is_exit = False

    def stop(self):          # 给外部调用的安全退出接口
        self.qmut.lock()
        self.is_exit = True
        self.qmut.unlock()
        self.wait()

    def run(self):
        while True:
            self.qmut.lock()
            if self.is_exit:
                self.qmut.unlock()
                break
            self.qmut.unlock()

            self._signal_update.emit(random.randint(0, 100))
            time.sleep(0.01)   # 20 Hz 刷新，肉眼就连续了
