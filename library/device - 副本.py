# coding=utf-8
__author__ = 'Xuxh'

import os
import sys
import logging
import time
import datetime
import subprocess
#import platform
#import smtplib
import signal
#from email import Encoders
import psutil
# from email.MIMEText import MIMEText
# from email.MIMEMultipart import MIMEMultipart
# from email.MIMEBase import MIMEBase
import re
import tempfile
from time import sleep
#from uiautomator import Device
import threading
import platform


import configuration
import myglobal
import self_uiautomator

PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)


# desktop.py
# def send_mail(subj, att):
#
#     smtp_server = CONFIG.getValue("Report","smtp")
#     sender = CONFIG.getValue("Report","sender")
#     recipients = CONFIG.getValue("Report","to")
#     passwd = CONFIG.getValue("Report","passwd")
#     recipients = recipients
#     session = smtplib.SMTP()
#     session.connect(smtp_server)
#     session.login(sender, passwd)
#     msg = MIMEMultipart()
#     msg['Subject'] = subj
#     msg.attach(MIMEText(subj,'plain-text'))
#     file = open(att, "r")
#     part = MIMEBase('application', "octet-stream")
#     part.set_payload(file.read())
#     Encoders.encode_base64(part)
#     part.add_header('Content-Disposition', 'attachment; filename="test_report.html"')
#     msg.attach(part)
#     smtpresult = session.sendmail('no-reply@dianhua.cn', recipients, msg.as_string())
#     session.close()

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

    def wifi_operation(self, action):

        if action == "OFF":
            cmd = "".join(["adb -s ", self.uid, " shell svc wifi disable "])
        if action == "ON":
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
            if action == "LAUNCH":
                cmd = "".join(["adb -s ", self.uid, " shell am start -n ", pname])
            if action == "CLOSE":
                cmd = "".join(["adb -s ", self.uid, " shell am force-stop ", self.pkg])
            if action == "INSTALL":
                cmd = "".join(["adb -s ", self.uid, " shell pm install -f ", path])
            if action == "CLEAR":
                cmd = "".join(["adb -s ", self.uid, " shell pm clear ", self.pkg])
            if action == "UNINSTALL":
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

        out = self.shellPIPE(cmd)

    def uninstall_app(self):

        try:
            pkg = self.CONFIG.getValue(self.uid,'apppackage')
            result =self.find_package()
            if result.find(pkg) != -1:
                self.app_operation('UNINSTALL')
        except Exception,ex:
            print ex

    def install_app(self,app_path):

        self.app_operation('INSTALL',app_path)
        sleep(2)
        self.app_operation(self.uid,'LAUNCH')
        sleep(2)


def kill_child_processes(parent_pid, sig=signal.SIGTERM):

    try:
        p = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    child_pid = p.children(recursive=True)

    for pid in child_pid:
        os.kill(pid.pid, sig)


def get_desktop_os_type():

    return platform.system()



# def handle_popup_windows(nub,device):
#
#     for i in range(nub):
#         d = Device(device)
#         el1 = d(text=u"安装")
#         el2 = d(text=u"信息")
#         e13 = d(text=u"允许")
#         if el1.exists:
#             el1.click()
#         if el2.exists:
#             el2.click()
#         if e13.exists:
#             e13.click()
#         sleep(1)

def do_popup_windows(nub,device):

    find_text = [u"安装",u"允许",u"跳过",u"继续",u"开启",u"欢迎"]

    for i in range(nub):
        self_uiautomator.click_popup_window(device,find_text)
        emulate_swipe_action(device)





def init_app(uid):

    uninstall_app(uid)
    # get path of app
    local_path = PATH('../apps/' + CONFIG.getValue(uid,'app'))
    mobile_path = CONFIG.getValue(uid,'mobile_app_path')
    device_file_operation(uid,'PUSH',local_path,mobile_path)
    app_path = os.path.join(mobile_path,CONFIG.getValue(uid,'app'))

    try:
        threads = []
        install = threading.Thread(target=install_app, args=(uid,app_path))
        proc_process = threading.Thread(target=do_popup_windows, args=(6,uid))
        threads.append(install)
        threads.append(proc_process)
        for t in threads:
            t.setDaemon(True)
            t.start()
            sleep(5)
        t.join()
    except Exception,ex:
        print ex

    app_operation(uid,'CLOSE')
    # delete APK file on mobile
    device_file_operation(uid,'DELETE',app_path,'')




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

def init_environment():

    desired_caps = {}
    desired_caps['platformName'] = 'Android'
    desired_caps['platformVersion'] = '5.1'
    desired_caps['deviceName'] = '860BCMK22LD8'
    #desired_caps['appPackage'] = 'com.UCMobile'
    #desired_caps['appActivity'] = 'com.UCMobile.main.UCMobile'
    desired_caps['appPackage'] = 'com.zhihu.android'
    desired_caps['appActivity'] = 'com.zhihu.android.app.ui.activity.MainActivity'
    #desired_caps['automationName']='Selendroid'
    #desired_caps['unicodeKeyboard']= True
    #desired_caps['resetKeyboard']= True
    #desired_caps['app'] = r'D:\UCBrowser.apk'
    desired_caps['app'] = r'D:\zhihu.apk'


    driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)

    return driver

# desktop.py
# def create_logger(filename):
#
#     logger = logging.getLogger("VlifeTest")
#     formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)
#     file_handler = logging.FileHandler(filename)
#     file_handler.setFormatter(formatter)
#     stream_handler = logging.StreamHandler(sys.stderr)
#     logger.addHandler(file_handler)
#     logger.addHandler(stream_handler)
#     logger.setLevel(logging.DEBUG)
#
#     return logger
#
#
# def get_log_name(device_name):
#
#     cur_date = datetime.datetime.now().strftime("%Y%m%d")
#     now = datetime.datetime.now().strftime("%Y%m%d%H%M")
#     parent_path = os.path.join('log',cur_date,device_name,now)
#
#     # create multi layer directory
#     if not os.path.isdir(parent_path):
#         os.makedirs(parent_path)
#
#     filename = os.path.join(parent_path,"testlog.txt")
#
#     return filename
#
#
# def launch_appium(uid, port, bport):
#
#     status = ""
#     try:
#         temp = "".join(["appium -p ", str(port), " -bp ", str(bport), " -U ",  uid, " --command-timeout 600"])
#         #temp = "".join(["node.exe ", js, " -p ", str(port), " -bp ", str(bport), " -U ",  uid, " --command-timeout 600"])
#         ap = subprocess.Popen(temp, shell=True)
#         time.sleep(4)
#         if ap.poll() is None:
#             status = "READY"
#     except Exception, ex:
#         print ex
#         status = "FAIL"
#         pid = None
#     return status, ap
#
#
# def close_all_nodes():
#
#     temp = ""
#
#     if platform.system() == "Windows":
#         temp = "taskkill /F /IM node.exe"
#     if platform.system() == "Linux":
#         temp = "killall node"
#     subprocess.Popen(temp, shell=True)
#     time.sleep(1)



if __name__ == '__main__':

    #out = update_android_time('048bf08709e8fe68',0)
    emulate_swipe_action('H536X60101234567')
    #screen_on_off('LRMRY5MNHEZP4LBU', 'OFF')
    #device_file_operation('HC37VW903116','PUSH', r'E:\AutoTestDemo\TestTasks\apps\420log.apk', '/data/local/tmp/')




