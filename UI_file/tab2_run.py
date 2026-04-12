import os
import copy
import csv
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5 import QtCore
from UI_file import tab2_ui

# tab2
class tab2Window(QWidget, tab2_ui.Ui_tab2_imageProcess):
    def __init__(self):
        super(tab2Window, self).__init__()
        tab2_ui.Ui_tab2_imageProcess.__init__(self)
        self.setupUi(self)
        self.testBtn.clicked.connect(self.test_func)
        self.applyTheme()

 
    def set_lib(self, lib, cur_ip, port, offline_flag):
        self.device_lib = lib
        self.machine_ip = cur_ip
        self.port = port
        self.offline_flag = offline_flag

    def test_func(self):
        print("测试tab2按钮被点击")
    
    def applyTheme(self):
        from run import ThemeManager
        theme = ThemeManager.getCurrentTheme()
        if theme == 'dark':
            pass
        else:
            pass
