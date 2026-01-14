from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5 import QtCore
import cv2 as cv
import numpy as np
import os
import sys
import importlib
from controlfile.func_create_data import UpdateDataThread

importlib.reload(sys)
Base_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(Base_DIR)
from UI_file import tab1_ui

# tab1
class tab1Window(QWidget, tab1_ui.Ui_tab1_imageProcess):
    def __init__(self):
        super(tab1Window, self).__init__()
        tab1_ui.Ui_tab1_imageProcess.__init__(self)
        self.setupUi(self)
        self.testbutton.clicked.connect(self.test)
        self.databuffer = []
        # 设置databuffer是固定长度的，超过长度则删除最旧的数据
        self.databuffer_max_len = 100
        
        # 设置画图熟悉
        self.plotView.setLabel('left', 'value')
        self.plotView.setLabel('bottom', 'time')
        self.plotView.setTitle('实时曲线')
        self.plotView.showGrid(x=True, y=True)
        
        # 设置y轴范围
        self.plotView.setYRange(0, 100, padding=0)
        
    def updateData(self, data):
        # 更新数据
        self.databuffer.append(data)
        if len(self.databuffer) > self.databuffer_max_len:
            self.databuffer.pop(0)

        # 关键：先清掉旧曲线，再画新曲线
        self.plotView.clear()                       # 1. 清屏
        x = np.arange(len(self.databuffer))
        y = np.array(self.databuffer)
        self.plotView.plot(x, y, clear=True)        # 2. 画新曲线

    def set_lib(self, lib, ip, port, offline_flag):
        self.device_lib = lib
        self.machine_ip = ip
        self.port = port
        self.offline_flag = offline_flag
        
    def test(self):
        print("测试按钮被点击")
        # 实时更新数据
        self.realdata_obj = UpdateDataThread()
        self.realdata_obj._signal_update.connect(self.updateData)

        self.realdata_obj.start()
        
