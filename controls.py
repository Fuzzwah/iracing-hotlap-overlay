#!python3
# -*- coding: utf-8 -*-

import sys
import overlay
from state import State
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow)
import ctypes
import drawers

class CamerasWindow(QtWidgets.QWidget):
    ir = None
    def __init__(self, ir, state, parent=None):
        super(CamerasWindow, self).__init__(parent)
        self.setWindowTitle('Cameras')
        self.ir = ir
        self.state = state
        self.setGeometry(1304, 30, 500, 100)
        lo = QtWidgets.QGridLayout()
        self.setLayout(lo)
        self.refresh_layout()

    def clear_layout(self):
        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            if not item:
                continue

            w = item.widget()
            if w:
                w.deleteLater()

    def refresh_layout(self):
        r, c = (0, 0)
        max_cols = 5
        self.clear_layout()
        lo = self.layout()
        button = QtWidgets.QPushButton('Refresh')
        button.clicked.connect(self.refresh_layout)
        lo.addWidget(button, r, c)

        c += 1

        for group in self.ir['CameraInfo']['Groups']:
            if c == max_cols:
                r += 1
                c = 0

            button = QtWidgets.QPushButton(group['GroupName'])
            button.clicked.connect(self.on_button_click)
            lo.addWidget(button, r, c)
            c += 1

        self.setLayout(lo)
#         groupIndex = ir['CamGroupNumber']-1
#         cameraIndex = ir['CamCameraNumber']-1
#
#         camGroup = ir['CameraInfo']['Groups'][groupIndex]
#         camera = camGroup['Cameras'][cameraIndex]

    def on_button_click(self):
        group = self.group_index_from_name(self.sender().text())
        car_index = self.ir['DriverInfo']['DriverCarIdx']
        car_num = str(self.ir['DriverInfo']['Drivers'][car_index]['CarNumber'])
        print(group, self.ir['DriverInfo']['DriverCarIdx'], car_num)
        if not self.ir.cam_switch_num(car_num, group, 0):
            raise ctypes.WinError()

    def group_index_from_name(self, name):
        index = 1
        for group in self.ir['CameraInfo']['Groups']:
            if group['GroupName'] == name:
                return index
            else:
                index += 1

class ControlsWindow(QtWidgets.QMainWindow):

    ir = None
    overlayWindow = None
    camerasWindow = None

    def __init__(self, ir, state, cfg, parent=None):
        super(ControlsWindow, self).__init__(parent)

        self.setWindowTitle('Director')
        self.ir = ir
        self.state = state
        self.cfg = cfg
        self.resize(300,100)
        self.show()

        self.overlayWindow = overlay.OverlayWindow()
        self.overlayWindow.show()

        self.camerasWindow = CamerasWindow(ir, state)
        self.camerasWindow.show()

        self.setCentralWidget(QtWidgets.QWidget(self))

        lo = QtWidgets.QGridLayout()
        self.centralWidget().setLayout(lo)

        clear_ui_button = QtWidgets.QPushButton('Clear User UI')
        clear_ui_button.clicked.connect(self.clearUserUI)
        lo.addWidget(clear_ui_button, 0, 0)

        clear_all_button = QtWidgets.QPushButton('Clear All')
        clear_all_button.clicked.connect(self.clearAll)
        lo.addWidget(clear_all_button, 0, 1)

        self.timestamp_cb = QtWidgets.QCheckBox('Show Timestamp')
        self.timestamp_cb.stateChanged.connect(self.toggleTimestamp)
        self.timestamp_cb.setChecked(False)
        lo.addWidget(self.timestamp_cb, 2, 0)

        self.lap_cb = QtWidgets.QCheckBox('Show Laps')
        self.lap_cb.stateChanged.connect(self.toggleLaps)
        self.lap_cb.setChecked(False)
        lo.addWidget(self.lap_cb, 3, 0)

        self.inputs_cb = QtWidgets.QCheckBox('Show Inputs')
        self.inputs_cb.stateChanged.connect(self.toggleInputs)
        self.inputs_cb.setChecked(False)
        lo.addWidget(self.inputs_cb, 4, 0)

        self.pos_cb = QtWidgets.QCheckBox('Show Positions')
        self.pos_cb.stateChanged.connect(self.togglePositions)
        self.pos_cb.setChecked(False)
        lo.addWidget(self.pos_cb, 5, 0)

        self.qual_cb = QtWidgets.QCheckBox('Show Qualifying Time')
        self.qual_cb.stateChanged.connect(self.toggleQualifyingTime)
        self.qual_cb.setChecked(False)
        lo.addWidget(self.qual_cb, 6, 0)

        self.qual_le = QtWidgets.QLineEdit()
        lo.addWidget(self.qual_le, 6, 1)

        self.setup_cb = QtWidgets.QCheckBox('Show Fuel/Setup')
        self.setup_cb.stateChanged.connect(self.toggleSetup)
        self.setup_cb.setChecked(False)
        lo.addWidget(self.setup_cb, 7, 0)

        self.setup_le = QtWidgets.QLineEdit()
        lo.addWidget(self.setup_le, 7, 1)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        lo.addWidget(line, 8, 0, 1, 2)

        self.tach_cb = QtWidgets.QCheckBox('Show Tach')
        self.tach_cb.stateChanged.connect(self.toggleTach)
        self.tach_cb.setChecked(True)
        lo.addWidget(self.tach_cb, 9, 0)

        self.green_cb = QtWidgets.QCheckBox('Show Green Background')
        self.green_cb.stateChanged.connect(self.toggleBackground)
        self.green_cb.setChecked(False)
        lo.addWidget(self.green_cb, 10, 0)

        self.file_cb = QtWidgets.QCheckBox('Write Relative to File')
        self.file_cb.stateChanged.connect(self.toggleFile)
        self.file_cb.setChecked(False)
        lo.addWidget(self.file_cb, 11, 0)

    def clearUserUI(self):
        self.lap_cb.setChecked(False)
        self.inputs_cb.setChecked(False)

    def clearAll(self):
        self.lap_cb.setChecked(False)
        self.inputs_cb.setChecked(False)
        self.positions_cb.setChecked(False)
        self.timestamp_cb.setChecked(False)


    def toggleDrawer(self, key, drawer):
        if (self.sender().isChecked()):
            self.overlayWindow.addDrawer(drawer, key)
        else:
            self.overlayWindow.removeDrawer(key)

    def toggleFile(self):
        self.toggleDrawer('file', drawers.FileDrawer(self.ir, self.state))

    def toggleBackground(self):
        self.toggleDrawer('bg', drawers.GreenScreenDrawer())

    def toggleQualifyingTime(self):
        self.toggleDrawer('qual', drawers.QualifyingTimeDrawer(self.ir, self.state, self.qual_le.text()))

    def toggleSetup(self):
        self.toggleDrawer('setup', drawers.SetupDrawer(self.ir, self.state, self.setup_le.text()))

    def toggleTimestamp(self):
        self.toggleDrawer('timestamp', drawers.TimeStampDrawer(self.ir, self.state))

    def toggleLaps(self):
        self.toggleDrawer('laps', drawers.LapDrawer(self.ir, self.state))

    def toggleInputs(self):
        self.toggleDrawer('inputs', drawers.InputsDrawer(self.ir, self.state))

    def togglePositions(self):
        self.toggleDrawer('positions', drawers.PositionsDrawer(self.ir, self.state))

    def toggleTach(self):
        self.toggleDrawer('tach', drawers.TachDrawer(self.ir, self.state, self.cfg['speed_units']))


    def closeEvent(self, event):
        self.overlayWindow.close()
        self.camerasWindow.close()

if __name__ == '__main__':
    app = QApplication([])
    win = ControlsWindow()
    win.show()
    sys.exit(app.exec_())
