# -*- coding: utf-8 -*-
import multiprocessing
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QFile, QIODevice
import pyqtgraph as pg
from UI_file.mainWindow import MainWindowShow
from ctypes import *

class CommonHelper:
    # 设置字体
    def __init__(self):
        pass

    @staticmethod
    def readQss(style):
        with open(style, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def loadFont(font_path):
        try:
            font_file = QFile(font_path)
            font_file.open(QIODevice.ReadOnly)
        except Exception as err:
            print(err)

class ThemeManager:
    _current_theme = 'dark'
    
    @staticmethod
    def getCurrentTheme():
        return ThemeManager._current_theme
    
    @staticmethod
    def setCurrentTheme(theme):
        ThemeManager._current_theme = theme
    
    @staticmethod
    def toggleTheme():
        ThemeManager._current_theme = 'light' if ThemeManager._current_theme == 'dark' else 'dark'
        return ThemeManager._current_theme

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        multiprocessing.freeze_support()
        self.mainWindow = MainWindowShow(None, None, None, None)
        self.mainWindow.show()

if __name__ == '__main__':
    pg.setConfigOption('background', 'w')
    pg.setConfigOptions(antialias=True)
    app = QApplication(sys.argv)
    # init style
    styleFile = r'.\resources\black_style.qss'
    qssStyle = CommonHelper.readQss(styleFile)
    app.setStyleSheet(qssStyle)
    mainWidget = MainWindow()
    sys.exit(app.exec_())
