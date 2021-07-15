import sys
import os
import shutil

from subprocess import Popen, PIPE, STDOUT
from PyQt5.QtCore import QThread, QWaitCondition, QMutex, pyqtSignal

dir_name = os.path.dirname(os.path.realpath(sys.argv[0]))    # 让打包后的exe能获取到路径


class CXYCmd(QThread):
    sitOut = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cmd = ''
        self.outs = ''

    def run(self):
        sp = Popen(self.cmd, stdout=PIPE, stderr=STDOUT, shell=True, universal_newlines=True)
        self.outs = sp.communicate()[0]
        self.sitOut.emit(self.outs)


class unThread(QThread):

    sinOut = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.devices = ''

    def run(self):
        # 卸载软件包
        wukong_pack = ['update', 'wukongcontrol', 'motorappplatform']
        cmd = dir_name + f'\\adb\\adb.exe -s {self.devices}:5555 uninstall com.chexiaoya.wukong.'
        for pack in wukong_pack:
            # print(cmd+pack)
            sp = Popen(cmd+pack, stdout=PIPE, stderr=STDOUT, shell=True, universal_newlines=True)
            strout = sp.communicate()
            # logging.debug('卸载线程结果：'+sp.returncode)
            s = strout[0].replace('\n', '')

            self.sinOut.emit(f'[{pack}]卸载：{s}')
        self.sinOut.emit(f'>> 设备[{self.devices}]卸载任务完成。\n')


class insThread(QThread):

    sinOut = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.devices = ''
        self.apkList = []
        self.apkfileList = []

    def run(self):
        try:
            # 复制文件
            for apkfile in self.apkfileList:
                apkName = apkfile.split('/')[-1]
                print(apkName)
                # 检测当前是否为默认目录，如果是，则退出复制流程
                print(os.path.normpath('./apk/'))
                if os.path.normpath(apkfile) == os.path.normpath('./apk/' + apkName):
                    self.sinOut.emit(f'>> 导入默认目录文件！')
                    break
                self.sinOut.emit(f'>> 导入[{apkName}] : success!')
                # 开始复制文件
                shutil.copy(apkfile, './apk/')

            self.sinOut.emit(('>> 开始安装导入的APK，请稍后...'))

            # 启动adb命令
            cmd = dir_name + f'/adb/adb.exe -s {self.devices} install -r ./apk/'
            for apk in self.apkList:
                # 使用Popen执行adb
                sp = Popen(cmd + apk, stdout=PIPE, stderr=STDOUT, shell=True, universal_newlines=True)
                for j in iter(sp.stdout):
                    self.sinOut.emit(j.replace('\n', ''))

            self.sinOut.emit(f'>> 设备[{self.devices}]安装任务结束。\n')

        except Exception as e:
            self.sinOut.emit(e)
