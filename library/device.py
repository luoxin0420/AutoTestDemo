#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Xuxh'

import datetime
import subprocess
import re
import tempfile
from time import sleep
import platform
import os
from os import path

import configuration
import myglobal


class Device(object):

    def __init__(self, uid):
        self.CONFIG = configuration.configuration()
        self.CONFIG.fileConfig(myglobal.CONFIGURATONINI)
        self.uid = uid
        self.pkg = self.CONFIG.getValue(uid,'apppackage')
        self.activity = self.CONFIG.getValue(uid,'appactivity')

    @staticmethod
    def shellPIPE(cmd):

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out

    @staticmethod
    def get_connected_devices():

        cmd = "adb devices"
        counter = 0
        devices =[]
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        for line in p.stdout.readlines():
            if len(line.strip()) > 0 and counter != 0:
                temp = line.split('device')
                devices.append(temp[0].strip())
            counter += 1
        return devices

    def getProcessId(self): # get the top activity PID

        cmd = 'adb -s {0} shell dumpsys activity top'.format(self.uid)
        out = self.shellPIPE(cmd)
        filename = ''.join([self.uid,datetime.now().strftime('%Y%m%d%H%M%S'),'top.txt'])
        curdir = os.getcwd()
        topProcessFile = path.join(curdir, filename)
        myFile = open(topProcessFile, 'w+')
        myFile.write(out)
        myFile.seek(0, 0);

        pid = ""

        for eachLine in myFile:
            if "pid=" in eachLine:
                activity = eachLine.split(" ")[3].strip()
                pid = eachLine.split("pid=")[-1].strip()
                break
        myFile.close()
        return pid

    def wifi_operation(self, action):

        if action.upper() == "OFF":
            cmd = "".join(["adb -s ", self.uid, " shell svc wifi disable "])
        if action.upper() == "ON":
            cmd = "".join(["adb -s ",self.uid," shell svc wifi enable "])
        try:

            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
        except Exception,ex:
            print ex

    def device_file_operation(self, action, orig_path, dest_path):

        if action.upper() == "PULL":
            cmd = "".join(["adb -s ", self.uid, " pull ",orig_path," ",dest_path])
        if action.upper() == "PUSH":
            cmd = "".join(["adb -s ", self.uid, " push ",orig_path," ", dest_path])
        if action.upper()== "DELETE":
            cmd = "".join(["adb -s ", self.uid, " shell rm ",orig_path])

        try:
            out_temp = tempfile.SpooledTemporaryFile(bufsize=10*1000)
            fileno = out_temp.fileno()
            p = subprocess.Popen(cmd, shell=True, stdout=fileno, stderr=subprocess.STDOUT)
            p.wait()
        except Exception,ex:
            print ex

    def app_operation(self,action,path=''):


        pname = ''.join([self.pkg, '/', self.activity])

        if self.pkg != "":
            if action.upper() == "LAUNCH":
                cmd = "".join(["adb -s ", self.uid, " shell am start -n ", pname])
            if action.upper() == "CLOSE":
                cmd = "".join(["adb -s ", self.uid, " shell am force-stop ", self.pkg])
            if action.upper() == "INSTALL":
                cmd = "".join(["adb -s ", self.uid, " shell pm install -f ", path])
            if action.upper() == "CLEAR":
                cmd = "".join(["adb -s ", self.uid, " shell pm clear ", self.pkg])
            if action.upper() == "UNINSTALL":
                cmd = "".join(["adb -s ", self.uid, " shell pm uninstall ", self.pkg])

            try:
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                p.wait()
            except Exception,ex:
                print ex

    def get_os_version(self):

        cmd = "".join(["adb -s ", self.uid, " shell getprop ro.build.version.release "])
        out = self.shellPIPE(cmd).split('.')

        if len(out) > 0:
            return int(out[0])
        else:
            return 0

    def get_screen_size(self):

        width = 0
        height = 0
        # cmd = "adb shell dumpsys window displays |head -n 3" (linux)
        # this command is supported above android 4.3, wm tool must be installed
        cmd = "".join(["adb -s ", self.uid, " shell wm size"])
        out = self.shellPIPE(cmd).split(':')
        if len(out) > 1:
            width, height = out[1].strip().split('x')
        return int(width),int(height)

    def emulate_swipe_action(self):

        # get resolution of screen
        width,height = self.get_screen_size()
        cmd = "adb -s {0} shell input swipe {1} {2} {3} {4}".format(self.uid,int(width/2),int(height/2),int(width/2),int(height/4))
        self.shellPIPE(cmd)
        sleep(2)

    def find_package(self):

        out = ''
        cmd = "".join(["adb -s ", self.uid, " shell pm list package ", self.pkg])
        out = self.shellPIPE(cmd)
        return out

    def screen_on_off(self, screen_action):
        sysstr = platform.system()
        if sysstr == "Windows ":
            cmd = "".join(["adb -s ", self.uid, " shell dumpsys power | findstr  ","Display"])
        elif sysstr == "Linux":
            cmd = "".join(["adb -s ", self.uid, " shell dumpsys power | grep  ","Display"])
        else:
            cmd=""

        if cmd != "":
            out = self.shellPIPE(cmd)
            if screen_action == "ON":
                while out.find("state=OFF") != -1:
                    cmd = "".join(["adb -s ", self.uid, " shell input keyevent 26"])
                    out = self.shellPIPE(cmd)
            elif screen_action == "OFF":
                while out.find("state=ON") != -1 :
                    cmd = "".join(["adb -s ", self.uid, " shell input keyevent 26"])
                    out = self.shellPIPE(cmd)

    def update_android_time(self,delta):

        # delta is interval time, like 1, -1
        interval_num = int(self.CONFIG.getValue(self.uid, 'frequence_num')) + int(delta)
        interval_unit = self.CONFIG.getValue(self.uid, 'frequence_unit')

        # get android time, then get expected time stamp
        cmd = "".join(["adb -s ", self.uid, " shell date +%Y%m%d.%H%M%S "])
        out = self.shellPIPE(cmd)
        for char in ['\r','\n']:
            out = out.replace(char,'')
        cur_time = datetime.datetime.strptime(out,'%Y%m%d.%H%M%S')
        if interval_unit.lower() == 'hour':
            expe_time = cur_time + datetime.timedelta(hours=interval_num)
        else:
            expe_time = cur_time + datetime.timedelta(days=interval_num)
        #time_stamp = time.mktime(expe_time.timetuple())
        version = self.get_os_version()

        if version < 6:
            expe_time = datetime.datetime.strftime(expe_time,'%Y%m%d.%H%M%S')
            cmd = 'adb -s {0} shell su 0 date -s {1} '.format(self.uid,expe_time)
        else:
            expe_time = datetime.datetime.strftime(expe_time,'%m%d%H%M%Y.00')
            cmd = 'adb -s {0} shell date {1} ; am broadcast -a android.intent.action.TIME_SET'.format(self.uid,expe_time)

        self.shellPIPE(cmd)

    def uninstall_app(self):

        try:
            pkg = self.CONFIG.getValue(self.uid,'apppackage')
            result =self.find_package()
            if result.find(pkg) != -1:
                self.app_operation('UNINSTALL')
        except Exception,ex:
            print ex

    def device_service_operation(self,action):

        service = self.CONFIG.getValue(self.uid,'service')

        if service != "":
            if action.upper() == "START":
                cmd = "".join(["adb -s ", self.uid, " shell am startservice -n ", service])
            if action.upper() == "STOP":
                cmd = "".join(["adb -s ", self.uid, " shell am stopservice -n ", service])
            self.shellPIPE(cmd)

    def get_device_screenshot(self,fname):

        cmd = "".join(["adb -s ",self.uid," shell /system/bin/screencap -p /sdcard/screenshot.png "])
        self.shellPIPE(cmd)
        cmd = "".join(["adb -s ",self.uid," pull /sdcard/screenshot.png ", fname])
        self.shellPIPE(cmd)


def get_userid_from_file(devicename):

    cmd = "".join(["adb -s ", devicename, " shell cat /data/data/com.vlife/shared_prefs/userinfo.xml"])
    out = Device.shellPIPE(cmd)
    keyword = r'.* <string name="uid">(.*)</string>.*'
    content = re.compile(keyword)
    for char in ['\r','\n']:
        out = out.replace(char,'')
    m = content.match(out)
    if m:
        userid = m.group(1)
    else:
        userid = ''

    return userid









