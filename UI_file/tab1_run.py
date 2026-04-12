from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5 import QtCore
import cv2 as cv
import numpy as np
import os
import sys
import importlib
import serial
import serial.tools.list_ports
import struct

# 协议常量
PROTOCOL_SOF = 0xAA
PROTOCOL_EOF = 0x55
PROTOCOL_FRAME_LENGTH = 20
PROTOCOL_DATA_MAX_LEN = 12

# 命令字定义
CMD_SET = 0x01
CMD_GET = 0x02
CMD_SET_ACK = 0x81
CMD_GET_ACK = 0x82
CMD_ERROR = 0xFF

# 参数ID定义
PARAM_POLE_PAIRS = 0x01
PARAM_SHUNT_RESISTANCE = 0x02
PARAM_OP_GAIN = 0x03
PARAM_MAX_CURRENT = 0x04
PARAM_ADC_REFERENCE = 0x05
PARAM_PWM_FREQUENCY = 0x06
PARAM_SPEED_CALC_FREQ = 0x07
PARAM_ADC_BITS = 0x08
PARAM_POSITION_CYCLE = 0x09

PARAM_POSITION_PID = 0x20
PARAM_SPEED_PID = 0x21
PARAM_TORQUE_D_PID = 0x22
PARAM_TORQUE_Q_PID = 0x23

PARAM_CONTROL_TYPE = 0x41
PARAM_TARGET_POSITION = 0x42
PARAM_TARGET_SPEED = 0x43
PARAM_TARGET_TORQUE_D = 0x44
PARAM_TARGET_TORQUE_Q = 0x45

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
        self.databuffer = []
        # 设置databuffer是固定长度的，超过长度则删除最旧的数据
        self.databuffer_max_len = 100
        
        self.serial = None
        
        # 预定义发送的数据串 (来自 simple_serial_tool.py)
        frame_data_str = "AA 01 43 01 00 00 96 43 00 00 00 00 00 00 00 00 1E 00 00 55"
        self.test_hex_data = bytes.fromhex(frame_data_str)
        
        # 串口相关按钮连接
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.toggle_serial)
        self.send_test_button.clicked.connect(self.send_test_frame)
        
        # 连接所有生成帧按钮
        self.pole_frame_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_POLE_PAIRS, 'float', [self.pole_pairs_value.value()]))
        self.r_shunt_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_SHUNT_RESISTANCE, 'float', [self.r_shunt_value.value()]))
        self.op_gain_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_OP_GAIN, 'float', [self.op_gain_value.value()]))
        self.max_current_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_MAX_CURRENT, 'float', [self.max_current_value.value()]))
        self.adc_reference_volt_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_ADC_REFERENCE, 'float', [self.adc_reference_volt_value.value()]))
        self.adc_bits_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_ADC_BITS, 'float', [self.adc_bits_value.value()]))
        
        self.pwm_freq_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_PWM_FREQUENCY, 'float', [self.moter_pwm_freq_value.value()]))
        self.speed_calc_freq_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_SPEED_CALC_FREQ, 'float', [self.moter_speed_calc_freq_value.value()]))
        self.position_cycle_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_POSITION_CYCLE, 'float', [self.position_cycle_value.value()]))
        
        self.control_type_CreateButton.clicked.connect(self.on_control_type_clicked)
        
        self.position_pid_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_POSITION_PID, 'float', [self.position_p_value.value(), self.position_i_value.value(), self.position_d_value.value()]))
        self.speed_pid_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_SPEED_PID, 'float', [self.speed_p_value.value(), self.speed_i_value.value(), self.speed_d_value.value()]))
        self.torque_D_pid_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_TORQUE_D_PID, 'float', [self.torque_d_p_value.value(), self.torque_d_i_value.value(), self.torque_d_d_value.value()]))
        self.torque_Q_pid_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_TORQUE_Q_PID, 'float', [self.torque_q_p_value.value(), self.torque_q_i_value.value(), self.torque_q_d_value.value()]))
        
        self.target_angle_position_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_TARGET_POSITION, 'float', [self.target_angle_position.value()]))
        self.target_speed_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_TARGET_SPEED, 'float', [self.target_speed_angle_perm.value()]))
        self.target_torque_D_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_TARGET_TORQUE_D, 'float', [self.target_torque_norm_d.value()]))
        self.target_torque_Q_CreateButton.clicked.connect(lambda: self.create_param_frame(PARAM_TARGET_TORQUE_Q, 'float', [self.target_torque_norm_q.value()]))
        
        # 存储当前生成的帧
        self.current_frame = None
        
        # 初始刷新串口
        self.refresh_ports()
        
        # 设置画图熟悉
        self.plotView.setLabel('left', 'value')
        self.plotView.setLabel('bottom', 'time')
        self.plotView.setTitle('实时曲线')
        self.plotView.showGrid(x=True, y=True)
        
        # 设置y轴范围
        self.plotView.setYRange(0, 100, padding=0)
        
    def refresh_ports(self):
        # 刷新可用串口列表
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.clear()
        self.port_combo.addItems(ports)

    def toggle_serial(self):
        # 打开/关闭串口
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None
            self.connect_button.setText("打开串口")
            print("串口已关闭")
            self.logtextEdit.append("串口已关闭")
        else:
            try:
                port = self.port_combo.currentText()
                if not port:
                    QMessageBox.warning(self, "警告", "请先选择串口！")
                    return
                baud = int(self.baud_combo.currentText())
                self.serial = serial.Serial(port, baud, timeout=1)
                self.connect_button.setText("关闭串口")
                print(f"成功打开串口: {port} (Baud: {baud})")
                self.logtextEdit.append(f"成功打开串口: {port} (Baud: {baud})")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开串口失败: {str(e)}")

    def send_test_frame(self):
        # 发送来自 simple_serial_tool.py 的测试帧
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(self.test_hex_data)
                print(f"已发送测试帧 : {self.test_hex_data.hex(' ').upper()}")
                self.logtextEdit.append(f"已发送测试帧 : {self.test_hex_data.hex(' ').upper()}")
            except Exception as e:
                QMessageBox.warning(self, "发送失败", f"串口发送失败: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "串口未打开，无法发送！")

    def calculate_checksum(self, cmd, param_id, data_len, data):
        """计算校验和"""
        checksum = cmd + param_id + data_len
        for i in range(12):  # 固定计算12个字节
            if i < len(data):
                checksum += data[i]
            else:
                checksum += 0
        return checksum & 0xFF

    def generate_frame(self, cmd, param_id, data_len, data):
        """生成协议帧"""
        frame = bytearray(PROTOCOL_FRAME_LENGTH)
        
        # 填充帧头
        frame[0] = PROTOCOL_SOF
        frame[1] = cmd
        frame[2] = param_id
        frame[3] = data_len
        
        # 填充数据段（固定12字节）
        for i in range(12):
            if i < len(data):
                frame[4 + i] = data[i]
            else:
                frame[4 + i] = 0
        
        # 计算校验和
        checksum = self.calculate_checksum(cmd, param_id, data_len, data)
        frame[16] = checksum
        
        # 填充保留字节
        frame[17] = 0
        frame[18] = 0
        
        # 填充帧尾
        frame[19] = PROTOCOL_EOF
        
        return frame

    def create_param_frame(self, param_id, data_type, values):
        """通用参数帧生成方法"""
        try:
            data = []
            for val in values:
                if data_type == 'float':
                    data.extend(list(struct.pack('<f', float(val))))
                elif data_type == 'int':
                    data.extend(list(struct.pack('<i', int(val))))
                elif data_type == 'uint8':
                    data.append(int(val) & 0xFF)
            
            # data_len 为参数个数
            data_len = len(values)
            
            # 生成帧
            self.current_frame = self.generate_frame(CMD_SET, param_id, data_len, data)
            
            # 显示结果
            hex_str = self.current_frame.hex(' ').upper()
            print(f"已生成参数帧 : {hex_str}, (ID: 0x{param_id:02X})")
            self.logtextEdit.append(f"已生成参数帧 : {hex_str}, (ID: 0x{param_id:02X})")
            self.test_hex_data = bytes.fromhex(hex_str)
            
            
        except Exception as e:
            QMessageBox.warning(self, "生成失败", f"帧生成失败: {str(e)}")

    def on_control_type_clicked(self):
        # 获取当前选中的控制类型
        if self.position_ctrl_radioButton.isChecked():
            control_type = 1.0
        elif self.speed_ctrl_radioButton.isChecked():
            control_type = 2.0
        elif self.torque_ctrl_radioButton.isChecked():
            control_type = 3.0
        elif self.speed_troque_radioButton.isChecked():
            control_type = 4.0
        elif self.pos_speed_torque_radioButton.isChecked():
            control_type = 5.0
        else:
            control_type = 0.0
        
        self.create_param_frame(PARAM_CONTROL_TYPE, 'float', [control_type])

    def set_lib(self, lib, ip, port, offline_flag):
        # 为数据解包做准备
        self.device_lib = lib
        self.machine_ip = ip
        self.port = port
        self.offline_flag = offline_flag

    def get_moter_control_params(self):
        # 将所有的参数保存到字典中
        params = {}
        moter_pole_pairs = int(self.pole_pairs_value.value())
        r_shunt = float(self.r_shunt_value.value())
        op_gain = float(self.op_gain_value.value())
        max_current = float(self.max_current_value.value())
        adc_reference_volt = float(self.adc_reference_volt_value.value())
        adc_bits = int(self.adc_bits_value.value())

        moter_pwm_freq = int(self.moter_pwm_freq_value.value())
        moter_speed_calc_freq = int(self.moter_speed_calc_freq_value.value())

        position_cycle = float(self.position_cycle_value.value() * 3.1415926)

        params['moter_params'] = {
            # 电机物理参数
            'pole_pairs': moter_pole_pairs, # 极对数
            # 电路参数
            'r_shunt': r_shunt, # 电流采样电阻，欧姆
            'op_gain': op_gain, # 运算放大倍数
            'max_current': max_current, # 最大q轴电流，安培
            'adc_reference_volt': adc_reference_volt, # 电流采样ADC参考电压，伏特
            'adc_bits': adc_bits, # ADC精度，bit
            # 单片机配置参数
            'pwm_freq': moter_pwm_freq, # 驱动桥pwm频率，Hz
            'speed_calc_freq': moter_speed_calc_freq, # 电机速度计算频率，Hz

            'position_cycle': position_cycle # 电机软件上的多圈周期，位置模式下能控制的范围，等于正半周期+负半周期
        }

        if self.position_ctrl_radioButton.isChecked():
            control_type = '0'
        elif self.speed_ctrl_radioButton.isChecked():
            control_type = '1'
        elif self.torque_ctrl_radioButton.isChecked():
            control_type = '2'
        elif self.speed_troque_radioButton.isChecked():
            control_type = '3'
        elif self.pos_speed_torque_radioButton.isChecked():
            control_type = '4'
        else:
            control_type = '1'

        params['control_type'] = control_type

        # PID控制参数
        position_p = self.position_p_value.value()
        position_i = self.position_i_value.value()
        position_d = self.position_d_value.value()

        speed_p = self.speed_p_value.value()
        speed_i = self.speed_i_value.value()
        speed_d = self.speed_d_value.value()
        
        torque_D_p = self.torque_d_p_value.value()
        torque_D_i = self.torque_d_i_value.value()
        torque_D_d = self.torque_d_d_value.value()

        torque_Q_p = self.torque_q_p_value.value()
        torque_Q_i = self.torque_q_i_value.value()
        torque_Q_d = self.torque_q_d_value.value()

        params['pid_params'] = {
            'position_p': position_p,
            'position_i': position_i,
            'position_d': position_d,

            'speed_p': speed_p,
            'speed_i': speed_i,
            'speed_d': speed_d,

            'torque_D_p': torque_D_p,
            'torque_D_i': torque_D_i,
            'torque_D_d': torque_D_d,

            'torque_Q_p': torque_Q_p,
            'torque_Q_i': torque_Q_i,
            'torque_Q_d': torque_Q_d
        }

        # 控制目标参数
        target_position = self.target_angle_position.value()
        target_speed = self.target_speed_angle_perm.value()
        target_normal_d = self.target_torque_norm_d.value()
        target_normal_q = self.target_torque_norm_q.value()

        params['target_params'] = {
            'target_position': target_position,
            'target_speed': target_speed,
            'target_normal_d': target_normal_d,
            'target_normal_q': target_normal_q
        }
        
        return params

