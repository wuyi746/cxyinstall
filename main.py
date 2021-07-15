import sys
import cgitb
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication

from bin.cxyinstall import CxyInstall


if __name__ == "__main__":
    cgitb.enable(format='text')
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    um = CxyInstall()
    um.show()
    sys.exit(app.exec_())
