#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
STM32 FOC 极简串口发送工具
用于测试特定协议帧的发送
"""

import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QTextEdit, QGroupBox)
from PyQt5.QtCore import QTimer

class SimpleSerialWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STM32 FOC 极简串口工具")
        self.setGeometry(200, 200, 500, 400)
        
        self.serial = None
        
        # 预定义发送的数据串
        self.hex_data = bytes.fromhex("AA 01 43 01 00 00 96 43 00 00 00 00 00 00 00 00 1E 00 00 55")
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        
        # 串口配置
        config_group = QGroupBox("串口配置")
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("端口:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        config_layout.addWidget(self.port_combo)
        
        config_layout.addWidget(QLabel("波特率:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "115200", "921600"])
        self.baud_combo.setCurrentText("115200")
        config_layout.addWidget(self.baud_combo)
        
        self.open_btn = QPushButton("打开串口")
        self.open_btn.clicked.connect(self.toggle_serial)
        config_layout.addWidget(self.open_btn)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # 发送控制
        send_group = QGroupBox("发送控制")
        send_layout = QVBoxLayout()
        
        hex_label = QLabel(f"发送内容 (Hex): {self.hex_data.hex(' ').upper()}")
        hex_label.setWordWrap(True)
        send_layout.addWidget(hex_label)
        
        self.send_btn = QPushButton("发送 HEX 数据")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_hex_data)
        send_layout.addWidget(self.send_btn)
        
        send_group.setLayout(send_layout)
        main_layout.addWidget(send_group)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        main_layout.addWidget(QLabel("日志:"))
        main_layout.addWidget(self.log_text)
        
        central_widget.setLayout(main_layout)
        
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        
    def toggle_serial(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None
            self.open_btn.setText("打开串口")
            self.send_btn.setEnabled(False)
            self.log("串口已关闭")
        else:
            try:
                port = self.port_combo.currentText()
                baud = int(self.baud_combo.currentText())
                self.serial = serial.Serial(port, baud, timeout=1)
                self.open_btn.setText("关闭串口")
                self.send_btn.setEnabled(True)
                self.log(f"成功打开串口: {port} (Baud: {baud})")
            except Exception as e:
                self.log(f"打开串口失败: {str(e)}")
                
    def send_hex_data(self):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(self.hex_data)
                self.log(f"已发送: {self.hex_data.hex(' ').upper()}")
            except Exception as e:
                self.log(f"发送失败: {str(e)}")
        else:
            self.log("错误: 串口未打开")
            
    def log(self, message):
        self.log_text.append(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleSerialWindow()
    window.show()
    sys.exit(app.exec_())
