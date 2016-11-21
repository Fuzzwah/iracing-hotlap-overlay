#!python3
# -*- coding: utf-8 -*-

from state import State
from PyQt5 import QtGui, QtCore
import math
import constants
import logging
import irsdk
import random
import configobj
from datetime import datetime

def timeFromStr(string):
    try:
        time_float = float(string)
    except ValueError:
        try:
            dt = datetime.strptime(string, '%M:%S.%f')
            time_float = dt.seconds + dt.microseconds
        except ValueError:
            print("Lap time needs to be in either M:SS.mmm or SSS.mmm format")

    return time_float

def strFromTime(time, decimal_places = 2):
    time = float(time)
    multiplier = pow(10, decimal_places)
    print(multiplier, decimal_places)
    s = int(time)
    ms = int((time - s) * multiplier)
    m, s = divmod(s, 60)
    if m > 0:
        result = '{}:{:02d}.{:03d}'.format(m, s, ms)
    else:
        result = '{}.{:03d}'.format(s, ms)
    return result


class TimeStampDrawer:
    def __init__(self, ir, state):
        self.ir = ir
        self.state = state

    def draw(self, widget):
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(255,255,255,96))
        p = QtGui.QPainter()
        p.begin(widget)
        p.setPen(pen)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        p.setFont(QtGui.QFont('Calibri', 8, QtGui.QFont.Normal))
        p.drawText(5,0,110,25, QtCore.Qt.AlignLeft, '%0.02f' % self.state.cur_session_time)
        p.end()


class GreenScreenDrawer:
    def __init__(self):
        pass

    def draw(self, widget):
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(0,255,0,255))
        p = QtGui.QPainter()
        p.begin(widget)
        p.setPen(pen)
        p.fillRect(0, 0, 1280, 720, constants.Color.GREEN_SCREEN)
        p.end()


class LapDrawer:
    def __init__(self, ir, state):
        self.ir = ir
        self.state = state

    def draw(self, widget):
        self.paintBackground(widget)
        self.paintRelativeText(widget)

    def paintBackground(self, widget):
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.fillRect(600, 22, 80, 22, constants.Color.GREY_TRANSPARENT)
        p.end()

    def paintRelativeText(self, widget):

        lap = self.ir['CarIdxLap'][self.state.cam_car_idx]
        if lap == self.state.session_laps:
            lap_str = 'FINAL LAP'
        elif lap > self.state.session_laps:
            lap_str = 'RACE OVER'
        else:
            lap_str = 'LAP %s/%s' % (lap, self.state.session_laps)
        p = QtGui.QPainter()
        if lap == 0:
            color = constants.Color.LIGHT_GREY
        elif lap > self.state.session_laps:
            color = constants.Color.LIGHT_GREY
        else:
            color = constants.Color.WHITE
        p.begin(widget)
        pen = QtGui.QPen()
        pen.setColor(color)
        p.setPen(pen)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        p.setFont(QtGui.QFont('Calibri', 10, QtGui.QFont.Bold))
        p.drawText(585,20,110,25, QtCore.Qt.AlignCenter, lap_str)
        p.end()


class QualifyingTimeDrawer:
    def __init__(self, ir, state, qual_time):
        self.ir = ir
        self.state = state
        self.outlap = self.ir['CarIdxLap'][self.state.cam_car_idx]
        self.start_time = -1

        if(len(qual_time) > 0):
            self.lap_time = timeFromStr(qual_time)
        else:
            self.lap_time = -1

    def draw(self, widget):
        self.paintBackground(widget)
        self.paintText(widget)

    def paintBackground(self, widget):
        lap = self.ir['CarIdxLap'][self.state.cam_car_idx]
        if lap == self.outlap:
            color = constants.Color.LIGHT_GREY
        elif lap == self.outlap + 2:
            color = constants.Color.GREEN
        else:
            color = constants.Color.YELLOW

        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.shear(math.radians(-10), 0)
        p.fillRect(585+3, 30, 110, 25, color)
        p.end()

    def paintText(self, widget):
        lap = self.ir['CarIdxLap'][self.state.cam_car_idx]
        if lap == self.outlap:
            str = '-.---'
        elif lap == self.outlap + 2:
            if self.lap_time == -1:
                self.lap_time = self.state.drivers[self.state.my_car_idx]['position_info']['FastestTime'] # self.state.cur_session_time - self.start_time

#             time = self.state.drivers[self.state.my_car_idx]['position_info']['FastestTime']
            str = strFromTime(self.lap_time, decimal_places=3)
#             self.state.drivers[self.state.my_car_idx]['position_info']['FastestTime']
        else:
            if self.start_time == -1:
                self.start_time = self.state.cur_session_time
            time = self.state.cur_session_time - self.start_time
            str = strFromTime(time, decimal_places=3)

        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        p.setFont(QtGui.QFont('Calibri', 14, QtGui.QFont.Bold))
        p.drawText(585-3,30,110,25, QtCore.Qt.AlignCenter, str)
        p.end()


class InputsDrawer:
    def __init__(self, ir, state):
        self.ir = ir
        self.state = state

    def draw(self, widget):
        self.paintBackground(widget)
        self.paintRelativeText(widget)

    def paintBackground(self, widget):
        offset = 10
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.shear(math.radians(-10), 0)
        # speed
        p.fillRect(30+offset, 30, 100, 55, constants.Color.YELLOW)
        # throttle
        p.fillRect(135+offset, 30, 135, 25, constants.Color.GREY_TRANSPARENT)
        p.fillRect(135+offset, 30, 135*self.ir['Throttle'], 25, constants.Color.GREEN)
        # brake
        p.fillRect(135+offset, 60, 135, 25, constants.Color.GREY_TRANSPARENT)
        p.fillRect(135+offset, 60, 135*self.ir['Brake'], 25, constants.Color.RED)
        # gear
        for i in range(0, 7):
            if i == (self.ir['Gear'] + 1):
                color = constants.Color.YELLOW
            else:
                color = constants.Color.GREY_TRANSPARENT
            p.fillRect(30+offset+35*i, 90, 30, 15, color)

        p.end()

    def paintRelativeText(self, widget):
        grey_color = constants.Color.GREY_TRANSPARENT
        yellow_color = constants.Color.YELLOW
        pen = QtGui.QPen()
        pen.setColor(grey_color)
        p = QtGui.QPainter()
        p.begin(widget)
        p.setPen(pen)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        # speed
        speed = int(round(self.ir['Speed']))
        p.setFont(QtGui.QFont('Calibri', 30, QtGui.QFont.Bold))
        p.drawText(30,32,72,55, QtCore.Qt.AlignRight, str(speed))
        # throttle
        pen.setColor(QtGui.QColor(36, 31, 32, 48))
        p.setPen(pen)
        p.setFont(QtGui.QFont('Calibri', 12, QtGui.QFont.Bold))
        p.drawText(145,33,135,25, QtCore.Qt.AlignLeft, 'THROTTLE')
        # brake
        p.drawText(145,63,135,25, QtCore.Qt.AlignLeft, 'BRAKE')
        # gear
        gear = self.ir['Gear'] + 1
        gear_strs = ('R', 'N', '1', '2', '3', '4', '5')
        p.setFont(QtGui.QFont('Calibri', 10, QtGui.QFont.Bold))
        for i in range(0, 7):
            if i == gear:
                color = grey_color
            else:
                color = yellow_color
            pen.setColor(color)
            p.setPen(pen)
            p.drawText(24+35*i,90,30,15, QtCore.Qt.AlignCenter, gear_strs[i])
        p.end()
        # kph
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        p.rotate(-90)
        pen = QtGui.QPen()
        pen.setColor(grey_color)
        p.setPen(pen)
        p.setFont(QtGui.QFont('Calibri', 10, QtGui.QFont.Bold))
        p.drawText(-72,104,135,25, QtCore.Qt.AlignLeft, 'KPH')
        p.end()


class PositionsDrawer:
    def __init__(self, ir, state):
        self.ir = ir
        self.state = state
        self.show_results = False

    def draw(self, widget):
        finished_drivers = self.getFinishedDriverInfo()
        if(len(finished_drivers)):
            drivers = [d for d in finished_drivers if d['position_info']['Lap'] == 0]
            if len(drivers) >= self.state.drivers_on_lead_lap:
                drivers = finished_drivers
            self.paintRelativeBackgrounds(widget, drivers)
            self.paintResultsText(widget, drivers)
        else:
            print(self.state.event_type)
            drivers = self.getDriverInfo()
            self.paintRelativeBackgrounds(widget, drivers)
            self.paintRelativeText(widget, drivers)

    def paintResultsText(self, widget, drivers):
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        for i, driver in enumerate(drivers):
            pos_info = driver['position_info']

            if pos_info['Position'] == 1:
                info = strFromTime(self.state.race_time)
            elif pos_info['Lap'] == 0:
                info = '-' + strFromTime(pos_info['Time'])
            else:
                info = '-%d L' % pos_info['Lap']

            if pos_info['CarIdx'] == self.state.my_car_idx:
                color = constants.Color.YELLOW
            else:
                color = constants.Color.WHITE

            pen = QtGui.QPen()
            pen.setColor(color)
            p.setPen(pen)
            p.setFont(QtGui.QFont('Calibri', 10, QtGui.QFont.Bold))
            width = 1280
            xpos = width - 265 + 5
            ypos = 20 + (16 * i) + 5
            p.drawText(xpos, ypos,30,25, QtCore.Qt.AlignLeft, str(i + 1))
            p.drawText(xpos + 20, ypos,30,25, QtCore.Qt.AlignLeft, '#%s' % (drivers[i]['driver_info']['CarNumber']))
            p.drawText(xpos + 55, ypos,160,25, QtCore.Qt.AlignLeft, drivers[i]['driver_info']['UserName'])
            p.drawText(xpos + 170, ypos,60,25, QtCore.Qt.AlignRight, info)
        p.end()

    def paintRelativeBackgrounds(self, widget, drivers):
        width = 1280
        xpos = width - 270
        ypos = 20
        height = len(drivers) * 16 + 10
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.fillRect(xpos, ypos, 250, height, constants.Color.GREY_TRANSPARENT)
        p.end()

    def paintRelativeText(self, widget, drivers):
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        for i in range(len(drivers)):
            if drivers[i]['position_info']['CarIdx'] == self.state.my_car_idx:
                color = constants.Color.YELLOW
            elif  drivers[i]['track_location'] == irsdk.TrkLoc.IN_PIT_STALL or drivers[i]['track_location'] == irsdk.TrkLoc.APROACHING_PITS:
                color = constants.Color.LIGHT_GREY
            else:
                color = constants.Color.WHITE
            pen = QtGui.QPen()
            pen.setColor(color)
            p.setPen(pen)
            p.setFont(QtGui.QFont('Calibri', 10, QtGui.QFont.Bold))
            width = 1280
            xpos = width - 265 + 5
            ypos = 20 + (16 * i) + 5
            p.drawText(xpos, ypos,30,25, QtCore.Qt.AlignLeft, drivers[i]['position'])
            p.drawText(xpos + 20, ypos,30,25, QtCore.Qt.AlignLeft, '#%d' % (drivers[i]['driver_info']['CarNumber']))
            p.drawText(xpos + 55, ypos,160,25, QtCore.Qt.AlignLeft, drivers[i]['driver_info']['UserName'])
            p.drawText(xpos + 180, ypos,50,25, QtCore.Qt.AlignRight, drivers[i]['gap'])
        p.end()

    def sort_by_lap_distance(self, diff):
        if diff < -.5:
            return diff + 1
        elif diff > .5:
            return diff - 1
        return diff

    def getFinishedDriverInfo(self):
        sorted_list = sorted([driver for driver in self.state.drivers.values() if driver['completed_race']], key=lambda d: d['position_info']['Position'])
        filtered_list = [driver for driver in sorted_list if driver['position_info']['Time'] >= 0]
        return filtered_list

    def getDriverInfo(self):
        drivers_by_position = sorted([d for d in self.state.drivers.values() if d['lap_distance'] != -1],
            reverse=True, key=lambda x: self.sort_by_lap_distance(x['overall_distance']))
        cur_pos = drivers_by_position.index(self.state.drivers[self.state.cam_car_idx])
        current_driver = drivers_by_position[cur_pos]
        metres_per_percent = self.state.track_length * 10
        driver_positions = []
        for i in range(0, len(drivers_by_position)):
            driver = drivers_by_position[i]
            driver['position'] = str(i + 1)
            # calc gap to current driver
            if not driver is current_driver:
                pct_dif = (driver['overall_distance'] - current_driver['overall_distance']) * 100
                dist = pct_dif * metres_per_percent
                gap = dist / (90 / 2.23693629)
                driver['gap'] = '{:0.01f}'.format(gap)
            else:
                driver['gap'] = ''
            driver_positions.append(driver)
        return driver_positions


class SetupDrawer:
    def __init__(self, ir, state, setup):
        self.ir = ir
        self.state = state
        self.setup = setup

    def draw(self, widget):
        self.paintBackground(widget)
        self.paintText(widget)

    def paintBackground(self, widget):
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.shear(math.radians(-10), 0)
        p.fillRect(1040 + (30 * math.tan(math.radians(10))), 30, 220, 25, constants.Color.GREY_TRANSPARENT)
        p.end()

    def paintText(self, widget):
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        pen = QtGui.QPen()
        pen.setColor(constants.Color.WHITE)
        p.setPen(pen)
        p.setFont(QtGui.QFont('Calibri', 12, QtGui.QFont.Bold))
        p.drawText(1042,32,220,25, QtCore.Qt.AlignLeft, self.setup)
        p.end()

    def paintRelativeBackgrounds(self, widget, drivers):
        for i in range(len(drivers)):
            if drivers[i]['position_info']['CarIdx'] == self.state.my_car_idx:
                color = constants.Color.YELLOW
            else:
                color = constants.Color.GREY_TRANSPARENT
            p = QtGui.QPainter()
            p.begin(widget)
            p.setRenderHint(QtGui.QPainter.Antialiasing)
            p.shear(math.radians(-10), 0)
            p.fillRect(1040 + (30 * math.tan(math.radians(10))) * i, 30 + 30 * i, 220, 25, color)
            p.end()

    def paintRelativeText(self, widget, drivers):
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        for i in range(len(drivers)):
            parts = drivers[i]['driver_info']['AbbrevName'].upper().partition(', ')
            if parts[2] != '':
                name = '%s %s' % (parts[2][:3], parts[0])
            else:
                name = parts[0][:3]
            name_num = '%s (#%s)' % (parts[0][:3], drivers[i]['driver_info']['CarNumber'])
            if drivers[i]['position_info']['CarIdx'] == self.state.my_car_idx:
                color = constants.Color.GREY
            else:
                color = constants.Color.WHITE
            pen = QtGui.QPen()
            pen.setColor(color)
            p.setPen(pen)
            p.setFont(QtGui.QFont('Calibri', 12, QtGui.QFont.Bold))
            p.drawText(1042,32 + 30 * i,30,25, QtCore.Qt.AlignLeft, drivers[i]['position'])
            p.drawText(1067,32 + 30 * i,160,25, QtCore.Qt.AlignLeft, name_num)
            p.drawText(1193,32 + 30 * i,50,25, QtCore.Qt.AlignRight, drivers[i]['gap'])
        p.end()

    def sort_by_lap_distance(self, diff):
        if diff < -.5:
            return diff + 1
        elif diff > .5:
            return diff - 1
        return diff

    def getFinishedDriverInfo(self):
        return sorted([driver for driver in self.state.drivers.values() if driver['completed_race']], key=lambda d: d['position_info']['Position'])

    def getDriverInfo(self):
        #todo: Needs to be fixed in case I need to pit
        drivers_by_position = sorted([d for d in self.state.drivers.values() if d['lap_distance'] != -1 and self.ir['CarIdxTrackSurface'][d['position_info']['CarIdx']] == irsdk.TrkLoc.ON_TRACK],
            reverse=True, key=lambda x: self.sort_by_lap_distance(x['overall_distance']))
        cur_pos = drivers_by_position.index(self.state.drivers[self.state.cam_car_idx])
        range_start = min(max(cur_pos - 2, 0), len(drivers_by_position) - 5)
        current_driver = drivers_by_position[cur_pos]
        metres_per_percent = self.state.track_length * 10
        driver_positions = []
        for i in range(range_start, range_start + 5):
            driver = drivers_by_position[i]
            driver['position'] = str(i + 1)
            # calc gap to current driver
            if not driver is current_driver:
                pct_dif = (driver['overall_distance'] - current_driver['overall_distance']) * 100
                dist = pct_dif * metres_per_percent
                gap = dist / (90 / 2.23693629)
                driver['gap'] = '{:0.01f}'.format(gap)
            else:
                driver['gap'] = ''
            driver_positions.append(driver)
        return driver_positions


class TachDrawer:

    def __init__(self, ir, state, speed_units):
        self.ir = ir
        self.state = state
        self.speed_units = speed_units
        self.initMaxSpeed = 55

        self.tach_bg_pm = QtGui.QPixmap()
        self.tach_bg_pm.load('images/tach-back.png')
        self.tach_fg_pm = QtGui.QPixmap()
        self.tach_fg_pm.load('images/tach-fore.png')

    def draw(self, widget):
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        # draw bg
        p.drawPixmap(50,50,300,300,self.tach_bg_pm)

        # draw throttle bar
        tw = round(self.ir['Throttle'] * 126)
        p.fillRect(137,260,tw,25,QtGui.QColor(0,255,0,255))

        # draw brake bar
        bw = round(self.ir['Brake'] * 126)
        p.fillRect(137,292,bw,25,QtGui.QColor(255,0,0,255))

        # draw rpm arc
        pc = (self.ir['RPM'] - 1000) / 6000
        ra = pc * -270
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(0,128,255,255))
        pen.setWidth(10)
        pen.setCapStyle(QtCore.Qt.FlatCap)
        p.setPen(pen)
        p.drawArc(85,83,230,230,(225*16),(ra*16))

        # draw foreground
        p.drawPixmap(50,50,300,300,self.tach_fg_pm)

        # draw speed
        if self.ir['Speed'] > self.initMaxSpeed:
            maxSpeed = self.ir['Speed']
        else:
            maxSpeed = self.initMaxSpeed

        if self.speed_units == 'mph':
            speed_units = 'mph'
            maxSpeed = maxSpeed * 2.236936
            speed = round(self.ir['Speed'] * 2.236936)
        elif self.speed_units == 'kph':
            speed_units = 'km/h'
            maxSpeed = maxSpeed * 3.6
            speed = round(self.ir['Speed'] * 3.6)
        else:
            speed_units = 'm/s'
            speed = round(self.ir['Speed'])
        pen.setColor(self.colorForPercent(speed/maxSpeed))
        p.setPen(pen)
        p.setFont(QtGui.QFont('Arial', 54))
        p.drawText(50,90,300,100, QtCore.Qt.AlignCenter, str(speed))

        # draw speed unit
        pen.setColor(QtGui.QColor(200,200,200,200))
        p.setPen(pen)
        p.setFont(QtGui.QFont('Arial', 15))
        p.drawText(50,130,300,100, QtCore.Qt.AlignCenter, speed_units)

        # draw gear
        pen.setColor(QtGui.QColor(255,255,255,255))
        p.setPen(pen)
        p.setFont(QtGui.QFont('Arial', 40))
        p.drawText(50,176,300,100, QtCore.Qt.AlignCenter, self.gear())

        p.end()

    def gear(self):
        raw_gear = self.ir['Gear']
        if raw_gear == -1:
            return 'R'
        elif raw_gear == 0:
            return 'N'
        else:
            return str(raw_gear)

    def colorForPercent(self, percent):
        if percent < 0.4:
            return QtGui.QColor(0,255,0,255)
        elif percent < 0.6:
            dif = 0.6 - percent
            pc = 1-(dif/0.2)
            return QtGui.QColor(round(pc * 255),255,0,255)
        elif percent < 0.8:
            return QtGui.QColor(255,255,0,255)
        elif percent < 0.95:
            dif = 0.95 - percent
            pc = (dif/0.15)
            return QtGui.QColor(255,round(pc * 255),0,255)
        else:
            return QtGui.QColor(255,0,0,255)

class FileDrawer:
    def __init__(self, ir, state):
        self.ir = ir
        self.state = state
        self.show_results = False

    def draw(self, widget):
        random.seed()
        if not random.randint(0, 100):
            return
        drivers = self.getDriverInfo()
        width = 250
        xpos = 0
        ypos = 0
        height = len(drivers) * 16 + 10
        img = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32)
        p = QtGui.QPainter(img)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.fillRect(xpos, ypos, 250, height, constants.Color.GREY_TRANSPARENT)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        for i in range(len(drivers)):
            if drivers[i]['position_info']['CarIdx'] == self.state.my_car_idx:
                color = constants.Color.YELLOW
            elif  drivers[i]['track_location'] == irsdk.TrkLoc.IN_PIT_STALL or drivers[i]['track_location'] == irsdk.TrkLoc.APROACHING_PITS:
                color = constants.Color.LIGHT_GREY
            else:
                color = constants.Color.WHITE
            pen = QtGui.QPen()
            pen.setColor(color)
            p.setPen(pen)
            p.setFont(QtGui.QFont('Calibri', 10, QtGui.QFont.Bold))
            xpos = 8
            ypos = (16 * i) + 5
            p.drawText(xpos, ypos,30,25, QtCore.Qt.AlignLeft, drivers[i]['position'])
            p.drawText(xpos + 20, ypos,30,25, QtCore.Qt.AlignLeft, '#%d' % (drivers[i]['driver_info']['CarNumber']))
            p.drawText(xpos + 55, ypos,160,25, QtCore.Qt.AlignLeft, drivers[i]['driver_info']['UserName'])
            p.drawText(xpos + 180, ypos,50,25, QtCore.Qt.AlignRight, drivers[i]['gap'])
        img.save("myimage.png", "PNG")
        del p

    def sort_by_lap_distance(self, diff):
        if diff < -.5:
            return diff + 1
        elif diff > .5:
            return diff - 1
        return diff

    def getFinishedDriverInfo(self):
        sorted_list = sorted([driver for driver in self.state.drivers.values() if driver['completed_race']], key=lambda d: d['position_info']['Position'])
        filtered_list = [driver for driver in sorted_list if driver['position_info']['Time'] >= 0]
        return filtered_list

    def getDriverInfo(self):
        drivers_by_position = sorted([d for d in self.state.drivers.values() if d['lap_distance'] != -1],
            reverse=True, key=lambda x: self.sort_by_lap_distance(x['overall_distance']))
        cur_pos = drivers_by_position.index(self.state.drivers[self.state.cam_car_idx])
        current_driver = drivers_by_position[cur_pos]
        metres_per_percent = self.state.track_length * 10
        driver_positions = []
        for i in range(0, len(drivers_by_position)):
            driver = drivers_by_position[i]
            driver['position'] = str(i + 1)
            # calc gap to current driver
            if not driver is current_driver:
                pct_dif = (driver['overall_distance'] - current_driver['overall_distance']) * 100
                dist = pct_dif * metres_per_percent
                gap = dist / (90 / 2.23693629)
                driver['gap'] = '{:0.01f}'.format(gap)
            else:
                driver['gap'] = ''
            driver_positions.append(driver)
        return driver_positions

