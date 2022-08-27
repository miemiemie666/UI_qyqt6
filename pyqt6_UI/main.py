
import serial  # 安装pyserial，但import serial，且不能安装serial
import serial.tools.list_ports
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QMessageBox, QCheckBox, QGraphicsView
from PyQt6.QtCore import QTimer, QDateTime
from ui import Ui_MainWindow

from PyQt6 import QtCharts
from PyQt6.QtCharts import QChartView
from PyQt6.QtCore import Qt


import pyqtgraph as pg
import numpy as np
import pandas as pd




class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__ui = Ui_MainWindow()
        self.__ui.setupUi(self)

        # 串口无效
        self.ser = None
        self.send_num = 0
        self.receive_num = 0
        self.receive_str = ''
        # 记录最后发送的回车字符的变量
        self.rcv_enter = ''
        
        ############变量区###########
        self.yPointNum=0 #y轴点数
        self.floatData=0 #浮点数据
        self.S1=[]
        self.S2=[]
        self.S3=[]
        self.S4=[]
        self.S5=[]
        self.S6=[]
        self.S7=[]
        self.S8=[]

        ###############################

        # 实例化一个定时器
        self.timer = QTimer(self)
        self.timer_send = QTimer(self)
        # 定时器调用读取串口接收数据
        self.timer.timeout.connect(self.recv)
        # 定时发送
        self.timer_send.timeout.connect(self.send)

        # 刷新一下串口的列表
        self.refresh()

        # 刷新串口外设按钮
        self.__ui.pushButton.clicked.connect(self.refresh)
        # 打开关闭串口按钮
        self.__ui.pushButton_2.clicked.connect(self.open_close)
        # 发送数据按钮
        self.__ui.pushButton_3.clicked.connect(self.send)
        # 清除窗口
        self.__ui.pushButton_4.clicked.connect(self.clear)
        # 保存数据
        self.__ui.pushButton_5.clicked.connect(self.txt_save)
        self.__ui.pushButton_6.clicked.connect(self.txt_save2)
        self.__ui.actionSave.triggered.connect(self.csv_save)
        # 定时发送
        self.__ui.checkBox_3.clicked.connect(self.send_timer_box)
        # 菜单栏Version
        self.__ui.actionVersion.triggered.connect(self.version)
        # 菜单栏Support
        self.__ui.actionSupport.triggered.connect(self.support)
        # 菜单栏K1,k2,Ca1,Ca2,Mg1,Mg2
        self.__ui.actionK1.triggered.connect(self.K1_detection)
        self.__ui.actionK2.triggered.connect(self.K2_detection)
        self.__ui.actionCa1.triggered.connect(self.Ca1_detection)
        self.__ui.actionCa2.triggered.connect(self.Ca2_detection)
        self.__ui.actionMg1.triggered.connect(self.Mg1_detection)
        self.__ui.actionMg2.triggered.connect(self.Mg2_detection)
        self.__ui.actionBlank.triggered.connect(self.Blank_detection)
        #######
        self.__ui.tabWidget.currentChanged.connect(self.graphDraw)

    ###########画图#############

    def graphDraw(self):
        pass


        
    




    # 检测串口
    def refresh(self):
        port_list = list(serial.tools.list_ports.comports())  # 检测串口
        if len(port_list) <= 0:
            print("No used com!")
        else:
            self.__ui.comboBox.clear()
            for port in port_list:
                self.__ui.comboBox.addItem(port[0])

    # 打开关闭串口
    def open_close(self, btn_sta):
        if btn_sta == True:
            try:
                # 输入参数'COM13',115200
                comNum = self.__ui.comboBox.currentText()
                baudRate = int(self.__ui.comboBox_2.currentText())
                dataBit = int(self.__ui.comboBox_3.currentText())
                parityBit = self.__ui.comboBox_4.currentText()
                stopBit = int(self.__ui.comboBox_5.currentText())
                self.ser = serial.Serial(comNum, baudRate, dataBit, parityBit, stopBit, timeout=0.2)
            except:
                QMessageBox.critical(
                    self, 'pycom', 'No serial port available or the current serial port is occupied')  # 没有可用的串口或当前串口被占用
                self.__ui.pushButton_2.setChecked(False)
                self.__ui.pushButton_2.setText("Open")
                return None

            # 字符间隔超时时间设置
            self.ser.interCharTimeout = 0.001
            # 1ms的测试周期
            self.timer.start(2)
            self.__ui.pushButton_2.setChecked(True)
            self.__ui.pushButton_2.setText("Close")
            print('open')
        else:
            # 关闭定时器，停止读取接收数据
            self.timer_send.stop()
            self.timer.stop()

            try:
                # 关闭串口
                self.ser.close()
            except:
                QMessageBox.critical(
                    self, 'pycom', 'Failed to close serial port')  # 关闭串口失败
                return None

            self.ser = None
            self.__ui.pushButton_2.setText("Open")
            print('close!')

    # 串口发送数据处理
    def send(self):
        '''
        未解决BUG:
        1.输入框是带格式输入的
        2.换行只能按回车，输入\r \n无效 (猜测是输入转码了)
        '''
        if self.ser != None:
            input_s = self.__ui.textEdit.toPlainText()
            if input_s != "":

                # 发送字符
                if (self.__ui.checkBox.isChecked() == False):
                    input_s = input_s.encode('utf-8')  # 没事别用gbk
                else:
                    # 发送十六进制数据
                    input_s = input_s.strip()  # 删除前后的空格
                    send_list = []
                    while input_s != '':
                        try:
                            num = int(input_s[0:2], 16)

                        except ValueError:
                            print('input hex data!')
                            # 请输入十六进制数据，以空格分开!
                            QMessageBox.critical(
                                self, 'pycom', 'input hex data!')
                            return None

                        input_s = input_s[2:]
                        input_s = input_s.strip()

                        # 添加到发送列表中
                        send_list.append(num)
                    input_s = bytes(send_list)

                print('Send:', input_s)
                # 发送数据
                try:
                    num = self.ser.write(input_s)
                except:

                    self.timer_send.stop()
                    self.timer.stop()
                    # 串口拔出错误，关闭定时器
                    self.ser.close()
                    self.ser = None

                    # 设置为打开按钮状态
                    self.pushButton_2.setChecked(False)
                    self.pushButton_2.setText("Open")
                    print('serial error send!')
                    return None

                self.send_num = self.send_num + num
                dis = 'Send: ' + \
                    '{:d}'.format(self.send_num) + '  Receive: ' + \
                    '{:d}'.format(self.receive_num)
                self.__ui.label_6.setText(dis)
                # print('send!')
            else:
                print('none data input!')

        else:
            # 停止发送定时器
            self.timer_send.stop()
            QMessageBox.critical(
                self, 'pycom', 'Please open the serial port')  # 请打开串口

    # 定时发送数据
    def send_timer_box(self):
        if self.__ui.checkBox_3.isChecked():
            time = self.__ui.lineEdit.text()

            try:
                time_val = int(time, 10)
            except ValueError:
                QMessageBox.critical(
                    self, 'pycom', 'Please enter a valid timing!')
                self.__ui.checkBox_3.setChecked(False)
                return None

            if time_val == 0:
                QMessageBox.critical(
                    self, 'pycom', 'Please enter a valid timing!')
                self.__ui.checkBox_3.setChecked(False)
                return None
            # 定时间隔发送
            self.timer_send.start(time_val)

        else:
            self.timer_send.stop()

    # 串口接收数据处理
    def recv(self):
        '''
        未解决bug:
        gbk发汉字,太多字会奔溃。
        '''
        try:
            num = self.ser.inWaiting()
        except:

            self.timer_send.stop()
            self.timer.stop()

            # 串口拔出错误，关闭定时器
            self.ser.close()
            self.ser = None

            # 设置为打开按钮状态
            self.__ui.pushButton_2.setChecked(False)
            self.__ui.pushButton_2.setText("Open")
            print('serial error!')
            return None
        if(num > 0):
            # 有时间会出现少读到一个字符的情况，还得进行读取第二次，所以多读一个
            data = self.ser.read(num)
            self.receive_str= data

            # 调试打印输出数据
            print('Receive:', data)
            num = len(data)
            ######################传出读取数据，给后面画图处理###2022.08.17##############
            
            
            yPointLimit = 1000 #y数据的最大个数

            if data.startswith(b'S2='): #判断是否是S2开头的数据  
                if self.yPointNum<yPointLimit:
                    self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S2.append(self.floatData)
                    #print(S2[len(S2)-1])
                if self.yPointNum>=yPointLimit:  #到上限以后，删1数据加1数据
                    #self.__ui.graphicsView.clear()
                    self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S2.append(self.floatData)
                    #print(S2[len(S2)-1])
                    self.S2=self.S2[1:] 
            if data.startswith(b'S3='): #判断是否是S2开头的数据  
                if self.yPointNum<yPointLimit:
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S3.append(self.floatData)
                    #print(S3[len(S3)-1])
                if self.yPointNum>=yPointLimit:  #到上限以后，删1数据加1数据
                    #self.__ui.graphicsView.clear()
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S3.append(self.floatData)
                    #print(S3[len(S3)-1])
                    self.S3=self.S3[1:] 
            if data.startswith(b'S4='): #判断是否是S4开头的数据  
                if self.yPointNum<yPointLimit:
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S4.append(self.floatData)
                    #print(S4[len(S4)-1])
                if self.yPointNum>=yPointLimit:  #到上限以后，删1数据加1数据
                    #self.__ui.graphicsView.clear()
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S4.append(self.floatData)
                    #print(S4[len(S4)-1])
                    self.S4=self.S4[1:] 
            if data.startswith(b'S5='): #判断是否是S5开头的数据  
                if self.yPointNum<yPointLimit:
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S5.append(self.floatData)
                    #print(S5[len(S5)-1])
                if self.yPointNum>=yPointLimit:  #到上限以后，删1数据加1数据
                    #self.__ui.graphicsView.clear()
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S5.append(self.floatData)
                    #print(S5[len(S5)-1])
                    self.S5=self.S5[1:] 
            if data.startswith(b'S6='): #判断是否是S6开头的数据  
                if self.yPointNum<yPointLimit:
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S6.append(self.floatData)
                    #print(S6[len(S6)-1])
                if self.yPointNum>=yPointLimit:  #到上限以后，删1数据加1数据
                    #self.__ui.graphicsView.clear()
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S6.append(self.floatData)
                    #print(S6[len(S6)-1])
                    self.S6=self.S6[1:] 
            if data.startswith(b'S7='): #判断是否是S7开头的数据  
                if self.yPointNum<yPointLimit:
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S7.append(self.floatData)
                    #print(S7[len(S7)-1])
                if self.yPointNum>=yPointLimit:  #到上限以后，删1数据加1数据
                    #self.__ui.graphicsView.clear()
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S7.append(self.floatData)
                    #print(S7[len(S7)-1])
                    self.S7=self.S7[1:] 
            if data.startswith(b'S8='): #判断是否是S8开头的数据  
                if self.yPointNum<yPointLimit:
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S8.append(self.floatData)
                    #print(S8[len(S8)-1])
                if self.yPointNum>=yPointLimit:  #到上限以后，删1数据加1数据
                    #self.__ui.graphicsView.clear()
                    #self.yPointNum=self.yPointNum+1
                    self.floatData=float(data[3:8])
                    self.S8.append(self.floatData)
                    #print(S8[len(S8)-1])
                    self.S8=self.S8[1:] 

            self.__ui.graphicsView.clear()
            self.__ui.graphicsView.setBackground('w')
            #self.__ui.graphicsView.showGrid(x=True, y=True)#显示网格
            self.__ui.graphicsView.setTitle('Open Circuit potentiometry')           
            self.__ui.graphicsView.setLabel("left", "Voltage")# 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
            self.__ui.graphicsView.setLabel("bottom", "Time")
            #self.__ui.graphicsView.plot(self.S1,pen=pg.mkPen('b') ) 
            self.__ui.graphicsView.plot(self.S2,pen=pg.mkPen(color=(0,0,0),width=3))  #blank black
            self.__ui.graphicsView.plot(self.S3,pen=pg.mkPen('r',width=3))             #Mg red
            self.__ui.graphicsView.plot(self.S8,pen=pg.mkPen(color=(255,165,0),width=3)) 
            self.__ui.graphicsView.plot(self.S5,pen=pg.mkPen('y',width=3) )            #K yellow
            self.__ui.graphicsView.plot(self.S6,pen=pg.mkPen('g',width=3) ) 
            self.__ui.graphicsView.plot(self.S4,pen=pg.mkPen('b',width=3) )         ##Ca blue
            self.__ui.graphicsView.plot(self.S7,pen=pg.mkPen(color=(139,0,255),width=3) ) 

            self.__ui.graphicsView.setYRange(0,0.7)
            if self.yPointNum>=800:   #point的个数到达一定值的时候，图右移
                self.__ui.graphicsView.setXRange(self.yPointNum-800,self.yPointNum)

 

            ######################################################################
            # 十六进制显示
            if self.__ui.checkBox_2.isChecked():
                out_s = ''
                for i in range(0, len(data)):
                    out_s = out_s + '{:02X}'.format(data[i]) + ' '
            else:
                # 串口接收到的字符串为b'123',要转化成unicode字符串才能输出到窗口中去
                out_s = data.decode('iso-8859-1')  # gbk，多字节速度快会崩溃，用iso-8859-1

                if self.rcv_enter == '\r':
                    # 上次有回车未显示，与本次一起显示
                    out_s = '\r' + out_s
                    self.rcv_enter = ''

                if out_s[-1] == '\r':
                    # 如果末尾有回车，留下与下次可能出现的换行一起显示，解决textEdit控件分开2次输入回车与换行出现2次换行的问题
                    out_s = out_s[0:-1]
                    self.rcv_enter = '\r'

            # 把字符串显示到窗口中去
            self.__ui.textBrowser.insertPlainText(out_s)


            # 统计接收字符的数量
            self.receive_num = self.receive_num + num
            dis = 'Send: ' + \
                '{:d}'.format(self.send_num) + '  Receive: ' + \
                '{:d}'.format(self.receive_num)
            self.__ui.label_6.setText(dis)
            # 先把光标移到到最后
            cursor = self.__ui.textBrowser.textCursor()
            cursor.selectionEnd()
            self.__ui.textBrowser.setTextCursor(cursor)
        else:
            # 此时回车后面没有收到换行，就把回车发出去
            if self.rcv_enter == '\r':
                # 先把光标移到到最后
                cursor = self.__ui.textBrowser.textCursor()
                cursor.selectionEnd()
                self.__ui.textBrowser.setTextCursor(cursor)
                self.__ui.textBrowser.insertPlainText('\r')
                self.rcv_enter = ''

     # 清除窗口操作
    def clear(self):
        if(self.__ui.tabWidget.currentIndex() == 0):
            self.__ui.textBrowser.clear()#清除接收窗口
            self.send_num = 0
            self.receive_num = 0
            dis = 'Send: ' + \
                '{:d}'.format(self.send_num) + '  Receive: ' + \
                '{:d}'.format(self.receive_num)
            self.__ui.label_6.setText(dis)
            '''
            self.__ui.graphicsView.clear()#清除图像 #太卡了，没有清除
            self.S1=self.S1[0:0]
            self.S2=self.S2[0:0]
            self.S3=self.S3[0:0]
            self.S4=self.S4[0:0]
            self.S5=self.S5[0:0]
            self.S6=self.S6[0:0]   
            self.S7=self.S7[0:0]
            self.S8=self.S8[0:0]
            '''

        elif(self.__ui.tabWidget.currentIndex() == 1):
            pass
        else:
            print("clear error!")

    # 保存数据
    def txt_save(self):
        if(self.__ui.tabWidget.currentIndex() == 0):
            try:
                txtFile = open('data.txt', 'w')
                strText = self.__ui.textBrowser.toPlainText()
                txtFile.write(strText)
                txtFile.close()

                QMessageBox.information(self, 'Tips', 'Succeed to save!')
            except:
                print('Failed tu save!')
                QMessageBox.warning(self, 'Tips', 'Failed to save!')
        elif(self.__ui.tabWidget.currentIndex() == 1):
            pass
        else:
            print("Save errror")

    def txt_save2(self):
        if(self.__ui.tabWidget.currentIndex() == 0):
            try:
                txtFile = open('data.txt', 'a')
                strText = self.__ui.textBrowser.toPlainText()
                txtFile.write(strText)
                txtFile.close()

                QMessageBox.information(self, 'Tips', 'Succeed to save!')
            except:
                print('Failed tu save!')
                QMessageBox.warning(self, 'Tips', 'Failed to save!')
        elif(self.__ui.tabWidget.currentIndex() == 1):
            pass
        else:
            print("Save errror")

    #data.txt to data.csv
    def csv_save(self):
        if(self.__ui.tabWidget.currentIndex() == 0):
            try:
                date = pd.read_table('data.txt', delimiter='=')
                index_1ist = list(set(date.index))
                index_1ist.sort() 
                #index_1ist.remove("Serial begin")
                dates ={} 
                for i in index_1ist: 
                    a=[]
                    for Serial, begin in date.iterrows(): 
                        Serial = str(Serial)
                        begin = float(begin)
                        if i == Serial:
                            a.append(begin)                       
                    dates[i] = a
                    del a
                #print(dates) 
                df = pd.DataFrame.from_dict(dates, orient='index')
                df.to_csv("data.csv")
                QMessageBox.information(self, 'Tips', 'Succeed to save!')
            except:
                print('Failed tu save!')
                QMessageBox.warning(self, 'Tips', 'Failed to save!')
        elif(self.__ui.tabWidget.currentIndex() == 1):
            pass
        else:
            print("Save errror")
    # 菜单栏Version
    def version(self):
        QMessageBox.information(
            self, 'Infos', 'Author: MIEMIEMIE\nVersion: V2.1\nTime: 10.08.2022\n')

    #菜单栏Support Demo
    def support(self):
        pw = pg.plot()
        # 设置图表标题、颜色、字体大小
        pw.setTitle("气温趋势", color='008080', size='12pt')           
        # 背景色改为白色
        pw.setBackground('w')
        # 显示表格线
        pw.showGrid(x=True, y=True)
        # 设置上下左右的label
        # 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
        pw.setLabel("left", "气温(摄氏度)")
        pw.setLabel("bottom", "时间")
        # 设置Y轴 刻度 范围
        pw.setYRange(min=-10, max=50)  
        # 创建 PlotDataItem ，缺省是曲线图
        curve = pw.plot( pen=pg.mkPen('b')) # 线条颜色
        hour = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        temperature = [30, 32, 34, 32, 33, 31, 29, 32, 35, 45]
        curve.setData(hour,  temperature )

###########################################20220819##########################################
    def K1_detection(self):
        pw = pg.plot()
        pw.setTitle("K+ Channel1", color='008080', size='12pt')   # 设置图表标题、颜色、字体大小        
        pw.setBackground('w')          # 背景色改为白色
        pw.showGrid(x=True, y=True)    # 显示表格线
        pw.setLabel("left", "voltage")        # 设置上下左右的label     
        pw.setLabel("bottom", "Time")       # 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
        #pw.setYRange(min=2,max=3) # 设置Y轴 刻度 范围
        curve = pw.plot(pen=pg.mkPen('b')) # 线条颜色
        curve.setData(self.S5)

    def K2_detection(self):
        pw = pg.plot()
        pw.setTitle("K+ Channel2", color='008080', size='12pt')   # 设置图表标题、颜色、字体大小        
        pw.setBackground('w')          # 背景色改为白色
        pw.showGrid(x=True, y=True)    # 显示表格线
        pw.setLabel("left", "voltage")        # 设置上下左右的label     
        pw.setLabel("bottom", "Time")       # 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
        #pw.setYRange(min=2,max=3) # 设置Y轴 刻度 范围
        curve = pw.plot(pen=pg.mkPen('b')) # 线条颜色
        curve.setData(self.S6)
    
    def Ca1_detection(self):
        pw = pg.plot()
        pw.setTitle("Ca2+ Channel1", color='008080', size='12pt')   # 设置图表标题、颜色、字体大小        
        pw.setBackground('w')          # 背景色改为白色
        pw.showGrid(x=True, y=True)    # 显示表格线
        pw.setLabel("left", "voltage")        # 设置上下左右的label     
        pw.setLabel("bottom", "Time")       # 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
        #pw.setYRange(min=2,max=3) # 设置Y轴 刻度 范围
        curve = pw.plot(pen=pg.mkPen('b')) # 线条颜色
        curve.setData(self.S4)

    def Ca2_detection(self):
        pw = pg.plot()
        pw.setTitle("Ca2+ Channel2", color='008080', size='12pt')   # 设置图表标题、颜色、字体大小        
        pw.setBackground('w')          # 背景色改为白色
        pw.showGrid(x=True, y=True)    # 显示表格线
        pw.setLabel("left", "voltage")        # 设置上下左右的label     
        pw.setLabel("bottom", "Time")       # 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
        #pw.setYRange(min=2,max=3) # 设置Y轴 刻度 范围
        curve = pw.plot(pen=pg.mkPen('b')) # 线条颜色
        curve.setData(self.S7)

    def Mg1_detection(self):
        pw = pg.plot()
        pw.setTitle("Mg2+ Channel1", color='008080', size='12pt')   # 设置图表标题、颜色、字体大小        
        pw.setBackground('w')          # 背景色改为白色
        pw.showGrid(x=True, y=True)    # 显示表格线
        pw.setLabel("left", "voltage")        # 设置上下左右的label     
        pw.setLabel("bottom", "Time")       # 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
        #pw.setYRange(min=2,max=3) # 设置Y轴 刻度 范围
        curve = pw.plot(pen=pg.mkPen('b')) # 线条颜色
        curve.setData(self.S3)

    def Mg2_detection(self):
        pw = pg.plot()
        pw.setTitle("Mg2+ Channel2", color='008080', size='12pt')   # 设置图表标题、颜色、字体大小        
        pw.setBackground('w')          # 背景色改为白色
        pw.showGrid(x=True, y=True)    # 显示表格线
        pw.setLabel("left", "voltage")        # 设置上下左右的label     
        pw.setLabel("bottom", "Time")       # 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
        #pw.setYRange(min=2,max=3) # 设置Y轴 刻度 范围
        curve = pw.plot(pen=pg.mkPen('b')) # 线条颜色
        curve.setData(self.S8)

    def Blank_detection(self):
        pw = pg.plot()
        pw.setTitle("Blank Channel", color='008080', size='12pt')   # 设置图表标题、颜色、字体大小        
        pw.setBackground('w')          # 背景色改为白色
        pw.showGrid(x=True, y=True)    # 显示表格线
        pw.setLabel("left", "voltage")        # 设置上下左右的label     
        pw.setLabel("bottom", "Time")       # 第一个参数 只能是 'left', 'bottom', 'right', or 'top'
        #pw.setYRange(min=2,max=3) # 设置Y轴 刻度 范围
        curve = pw.plot(pen=pg.mkPen('b')) # 线条颜色
        curve.setData(self.S2)
###############################################################################################


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mymainWindow = MyMainWindow()
    mymainWindow.show()
    sys.exit(app.exec())
