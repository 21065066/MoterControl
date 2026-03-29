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
        self.databuffer = []
        # 设置databuffer是固定长度的，超过长度则删除最旧的数据
        self.databuffer_max_len = 100
        self.set_pushButton.clicked.connect(self.set_param_func)
        
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
    
    def set_param_func(self):
        param_dict = self.get_moter_control_params()
        print(param_dict)

