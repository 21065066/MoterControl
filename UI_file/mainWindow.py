from PyQt5.QtWidgets import *
from UI_file import imageProcess
from UI_file.tab1_run import tab1Window
from UI_file.tab2_run import tab2Window
import xml.etree.ElementTree as ET


class MainWindowShow(QMainWindow, imageProcess.Ui_imageProcess):
    def __init__(self, ip_addr, wrt_lib, name, port):
        super(MainWindowShow, self).__init__()
        imageProcess.Ui_imageProcess.__init__(self)
        self.setupUi(self)
        self.wrt_lib = wrt_lib
        self.ip_addr = ip_addr
        self.port = port
        self.select_win = None
        self.offline_flag = False
        self.tab_list_name = ['经典PID', '新控制算法'] # tab1,tab2,tab3 子页名称显示
        self.init_tab()

    def init_tab(self):
        tab_status = []
        xml_status = [1, 1] # 表示tab1,tab2是否显示
        for i in range(len(xml_status)):
            if int(xml_status[i]) == 1:
                tab_status.append(True)
            else:
                tab_status.append(False)
        self.view_tab(tab_status)

    def create_tab(self, tab_index):
        # 动态获取窗口类
        class_name = f"tab{tab_index + 1}Window"
        try:
            tab_class = globals()[class_name]
            tab = tab_class()
            tab.set_lib(self.wrt_lib, self.ip_addr, self.port, self.offline_flag)
            self.tabWidget.addTab(tab, self.tab_list_name[tab_index])
            return tab
        except KeyError:
            return None

    def view_tab(self, tab_state):
        # 清空布局
        while self.horizontalLayout.count():
            item = self.horizontalLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if self.select_win is not None:
            self.select_win.close()
        # print("tab status:", tab_state)
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        for index, status in enumerate(tab_state):
            if status:
                if index == 10:
                    continue
                self.create_tab(index)
        self.horizontalLayout.addWidget(self.tabWidget)
    
    def applyTheme(self):
        from run import ThemeManager
        for i in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(i)
            if hasattr(tab, 'applyTheme'):
                tab.applyTheme()

