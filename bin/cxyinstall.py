import os
import json
import re
import time

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt

from bin.threads import insThread, unThread, CXYCmd
from ui.ui_cxyinstall import Ui_MainWindow

dir_name = os.getcwd()   # 获取脚本所在目录
print(dir_name)


class CxyInstall(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # IP列表
        # 连接设备
        self.conBtn.clicked.connect(self.con_dev)
        # IP列表
        self.ipList.clicked.connect(self.sel_item)
        # 加载iplist
        with open('data/IPlist.json', 'r', encoding='utf-8') as ips:
            # json.dump()
            self.IPData = json.loads(ips.read())
            self.ipList.addItems(self.IPData['history'])

        # 初始化载入的设备全部置灰
        for c in range(0, self.ipList.count()):
            self.ipList.item(c).setForeground(QColor('grey'))

        # 安装卸载
        # 安装
        self.insBtn.clicked.connect(self.cxy_install)
        # 清理车机数据
        self.clearBtn.clicked.connect(self.clear_date)
        # 浏览
        self.findAPKPathBtn.clicked.connect(self.find_apk_path)
        # 卸载
        self.unBtn.clicked.connect(self.cxy_uninstall)

        self.un_thr = unThread()
        self.un_thr.sinOut.connect(self.devLogBrowser.append)
        self.in_thr = insThread()
        self.in_thr.sinOut.connect(self.devLogBrowser.append)
        self.cmd_thr = CXYCmd()

    # 浏览目录
    def find_apk_path(self):
        ins_file = self.insPath.text()
        if ins_file:
            dev_file = QFileDialog.getExistingDirectory(self, "浏览", ins_file)
        else:
            dev_file = QFileDialog.getExistingDirectory(self, "浏览", './')
        if dev_file:
            self.insPath.setText(dev_file)

    # 清理车机数据
    def clear_date(self):
        ms = QMessageBox.question(self, '警告！', '是否清理车机数据！', QMessageBox.Yes, QMessageBox.No)
        if ms == QMessageBox.Yes:
            self.devLogBrowser.append('* 开始清理车机数据')
            if self.ipText.text():
                packages = ['com.chexiaoya.wukong.wukongcontrol',
                            'com.chexiaoya.wukong.motorappplatform',
                            'com.chexiaoya.wukong.update']
                for pack in packages:
                    res = self.win_cmd(f'.\\adb\\adb.exe -s \
                        {self.ipText.text()}:5555 shell pm clear {pack}')\
                            .replace("\n", "")
                    self.devLogBrowser.append(f'[{pack}]清理结果:{res}')
                self.devLogBrowser.append('>> 车机清理结束')
            else:
                self.devLogBrowser.append('>> 请选择有效设备IP')

    # 卸载车小丫应用
    def cxy_uninstall(self):
        # 调用卸载线程
        ms = QMessageBox.question(self, '警告', '是否继续卸载', QMessageBox.Yes, QMessageBox.No)
        if ms == QMessageBox.Yes:
            self.devLogBrowser.append('* 开始卸载：')
            if not self.ipText.text():
                return self.devLogBrowser.append('>> 警告：异常操作，请选择并连接设备IP！\n')

            if self.in_thr.isRunning() is False and self.un_thr.isRunning() is False:
                self.un_thr.devices = self.ipText.text()
                self.un_thr.start()
            else:
                QMessageBox.warning(self, '>> 警告：安装或卸载中，\
                    请勿重复操作！\n', QMessageBox.Yes)

    # 安装目录下的应用
    def cxy_install(self):
        # 复制文件
        apk_list, apk_file_list = self.copy_apk()
        # 判断in_thr和un_thr线程是否正在运行，如果没运行则开始进如安装流程
        if self.in_thr.isRunning() is False and self.un_thr.isRunning() is False:
            if len(apk_list) > 0:
                self.devLogBrowser.append('* 开始安装应用')
                # 指定设备IP，安装应用，启动安装线程
                self.in_thr.apkList = apk_list
                self.in_thr.apkfileList = apk_file_list
                self.in_thr.devices = self.ipText.text()
                self.in_thr.start()
        else:
            QMessageBox.warning(self, '>> 警告：安装或卸载中，请勿重复操作！\n', QMessageBox.Yes)

    def sel_item(self):
        self.ipText.setText(self.ipList.currentItem().text())

    def con_dev(self):
        # 连接设备
        self.devLogBrowser.append('* 设备连接中...')
        devices = self.ipText.text()
        # 判断输入ip是否正确
        ip_re = r'(?:\d{1,3}\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)'
        if re.findall(ip_re, devices):
            self.win_cmd(dir_name + f'/adb/adb.exe connect {devices}:5555')
        else:
            self.devLogBrowser.append('>> 未检测到新增的合法ip地址，开始载入已连接设备：')
        # 通过正则获取adb devces列表里的ip设备
        all_dev = self.win_cmd(dir_name + f'/adb/adb.exe devices')
        result = re.findall(ip_re, all_dev)
        print(result)

        if not result:
            return self.devLogBrowser.append('>> 警告：ADB没有连接任何设备！\n')

        # 判断result中的ip是否存在历史记录
        for ip in result:
            if ip in self.IPData['history']:
                for f in self.ipList.findItems(ip, Qt.MatchContains):  # 根据连接的ip搜索历史记录，并遍历
                    ip_row = self.ipList.row(f)  # 获取历史记录后，查找该记录所在的行
                    self.ipList.item(ip_row).setForeground(QColor('black'))  # 根据行，更改ip字体颜色
            else:
                print(ip)
                self.ipList.addItem(ip)  # 不存在历史就表，则添加该ip到listwidget控件中
                self.IPData['history'].append(ip)
                print(self.IPData['history'])
                with open('./data/IPlist.json', 'w', encoding='utf-8') as resf:
                    resf.write(json.dumps(self.IPData))

        for res in result:
            self.devLogBrowser.append('>> 加载成功：'+res)
        self.devLogBrowser.append('>> 设备加载结束！\n')

    # 复制apk文件到本地目录
    def copy_apk(self):
        in_sp = self.insPath.text().replace('\\', '/')
        apk_list = []    # 存储apk文件名
        apk_file_list = []  # 存储检测到的apk绝对路径
        self.devLogBrowser.append('* 安装文件导入中...：')
        if not self.ipText.text():
            return self.devLogBrowser.append('>> 错误：请选择并连接设备IP！\n')
        elif not in_sp:
            # 安装目录为空时，指派默认目录
            in_sp = './apk'

        if in_sp.find('.apk') == -1:
            # 判断路径为真实路径
            if os.path.isdir(in_sp):
                # os.walk(in_sp)遍历in sp路径，需要3个函数接收，root为目录，files文件名List
                for root, dirs, files in os.walk(in_sp):
                    # files 为in_sp目录下所有文件
                    for f in files:
                        # 判断后缀为apk的文件名，并添加到apklist，传给insThread安装线程使用
                        if os.path.splitext(f)[1] == '.apk':
                            apk_list.append(f)
                            apk_file_list.append(root+'/'+f)
            else:
                self.devLogBrowser.append('>> 错误：无效目录！')
        else:
            # 剪切路径中的apk名字，加入到apk list
            apk_name = in_sp.split('/')[-1]
            apk_list.append(apk_name)
            apk_file_list.append(in_sp)

        if len(apk_file_list) == 0:
            self.devLogBrowser.append('>> 警告：未检测到APK文件！')

        return apk_list, apk_file_list

    def win_cmd(self, cmd):
        self.cmd_thr.cmd = cmd
        self.cmd_thr.start()
        # 增加循环，避免该线程没跑完，就跳入到下一步，导致结果出现异常。
        while True:
            if self.cmd_thr.isFinished():
                return self.cmd_thr.outs
            time.sleep(1)
