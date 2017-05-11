# coding=utf-8
__author__ = 'Xuxh'

import os
import sys
import logging
import time
import datetime
import subprocess
import platform
import smtplib
import signal
from email import Encoders
import psutil
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
import re
import tempfile
from time import sleep
from uiautomator import Device
import threading


import configuration
import myglobal
import self_uiautomator

PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)

CONFIG = configuration.configuration()
CONFIG.fileConfig(myglobal.CONFIGURATONINI)

def send_mail(subj, att):

    smtp_server = CONFIG.getValue("Report","smtp")
    sender = CONFIG.getValue("Report","sender")
    recipients = CONFIG.getValue("Report","to")
    passwd = CONFIG.getValue("Report","passwd")
    recipients = recipients
    session = smtplib.SMTP()
    session.connect(smtp_server)
    session.login(sender, passwd)
    msg = MIMEMultipart()
    msg['Subject'] = subj
    msg.attach(MIMEText(subj,'plain-text'))
    file = open(att, "r")
    part = MIMEBase('application', "octet-stream")
    part.set_payload(file.read())
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="test_report.html"')
    msg.attach(part)
    smtpresult = session.sendmail('no-reply@dianhua.cn', recipients, msg.as_string())
    session.close()


def kill_child_processes(parent_pid, sig=signal.SIGTERM):

    try:
        p = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    child_pid = p.children(recursive=True)

    for pid in child_pid:
        os.kill(pid.pid, sig)


def wifi_operation(uid, action):


    if action == "OFF":
        cmd = "".join(["adb -s ", uid, " shell svc wifi disable "])
    if action == "ON":
        cmd = "".join(["adb -s ",uid," shell svc wifi enable "])
    try:

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
    except Exception,ex:
        print ex


def device_file_operation(uid, action, orig_path, dest_path):

    if action.upper() == "PULL":
        cmd = "".join(["adb -s ", uid, " pull ",orig_path," ",dest_path])
    if action.upper() == "PUSH":
        cmd = "".join(["adb -s ", uid, " push ",orig_path," ", dest_path])

    try:
        out_temp = tempfile.SpooledTemporaryFile(bufsize=10*1000)
        fileno = out_temp.fileno()
        p = subprocess.Popen(cmd, shell=True, stdout=fileno, stderr=subprocess.STDOUT)
        p.wait()
    except Exception,ex:
        print ex


def app_operation(uid,action,path=''):

    pkg = CONFIG.getValue(uid,'apppackage')
    activity = CONFIG.getValue(uid,'appactivity')

    pname = ''.join([pkg, '/', activity])

    if pkg != "":
        if action == "LAUNCH":
            cmd = "".join(["adb -s ", uid, " shell am start -n ", pname])
        if action == "CLOSE":
            cmd = "".join(["adb -s ", uid, " shell am force-stop ", pkg])
        if action == "INSTALL":
            cmd = "".join(["adb -s ", uid, " shell pm install -f ", path])
        if action == "CLEAR":
            cmd = "".join(["adb -s ", uid, " shell pm clear ", pkg])
        if action == "UNINSTALL":
            cmd = "".join(["adb -s ", uid, " shell pm uninstall ", pkg])

        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
        except Exception,ex:
            print ex


def shellPIPE(cmd):

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out


def find_package(uid):

    out = ''
    pkg = CONFIG.getValue(uid,'apppackage')
    cmd = "".join(["adb -s ", uid, " shell pm list package ", pkg])
    out = shellPIPE(cmd)
    return out


def handle_popup_windows(nub,device):

    for i in range(nub):
        d = Device(device)
        el1 = d(text=u"安装")
        el2 = d(text=u"信息")
        e13 = d(text=u"允许")
        if el1.exists:
            el1.click()
        if el2.exists:
            el2.click()
        if e13.exists:
            e13.click()
        sleep(1)


def do_popup_windows(nub,device):

    find_text = [u"安装",u"允许",u"跳过"]

    for i in range(nub):
        self_uiautomator.click_popup_window(device,find_text)


def uninstall_app(uid):

    try:
        pkg = CONFIG.getValue(uid,'apppackage')
        result =find_package(uid)
        if result.find(pkg) != -1:
            app_operation(uid,'UNINSTALL')
    except Exception,ex:
        print ex


def install_app(uid,app_path):


    app_operation(uid,'INSTALL',app_path)
    sleep(2)
    app_operation(uid,'LAUNCH')
    sleep(2)



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
        proc_process = threading.Thread(target=do_popup_windows, args=(5,uid))
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


def update_android_time(uid,delta):

    # delta is interval time, like 1, -2
    interval_num = int(CONFIG.getValue(uid, 'frequence_num')) + int(delta)
    interval_unit = CONFIG.getValue(uid, 'frequence_unit')

    # get android time, then get expected time stamp
    cmd = "".join(["adb -s ", uid, " shell date +%Y%m%d.%H%M%S "])
    out = shellPIPE(cmd)
    for char in ['\r','\n']:
        out = out.replace(char,'')
    cur_time = datetime.datetime.strptime(out,'%Y%m%d.%H%M%S')
    if interval_unit.lower() == 'hour':
        expe_time = cur_time + datetime.timedelta(hours=interval_num)
    else:
        expe_time = cur_time + datetime.timedelta(days=interval_num)
    #time_stamp = time.mktime(expe_time.timetuple())
    expe_time = datetime.datetime.strftime(expe_time,'%Y%m%d.%H%M%S')

    #  adb shell date $(date +%m%d%H%M%Y), set random date
    # set new time on mobile
    #cmd = 'adb -s {0} shell date {1} ; am broadcast -a android.intent.action.TIME_SET'.format(uid,time_stamp) # not working
    cmd = 'adb -s {0} shell su 0 date -s {1} '.format(uid,expe_time)
    out = shellPIPE(cmd)


def get_userid_from_file(devicename):

    cmd = "".join(["adb -s ", devicename, " shell cat /data/data/com.vlife/shared_prefs/userinfo.xml"])
    out = shellPIPE(cmd)
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


def create_logger(filename):

    logger = logging.getLogger("VlifeTest")
    formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)

    return logger


def get_log_name(device_name):

    cur_date = datetime.datetime.now().strftime("%Y%m%d")
    now = datetime.datetime.now().strftime("%Y%m%d%H%M")
    parent_path = os.path.join('log',cur_date,device_name,now)

    # create multi layer directory
    if not os.path.isdir(parent_path):
        os.makedirs(parent_path)

    filename = os.path.join(parent_path,"testlog.txt")

    return filename


def launch_appium(uid, port, bport):

    status = ""
    try:
        temp = "".join(["appium -p ", str(port), " -bp ", str(bport), " -U ",  uid, " --command-timeout 600"])
        #temp = "".join(["node.exe ", js, " -p ", str(port), " -bp ", str(bport), " -U ",  uid, " --command-timeout 600"])
        ap = subprocess.Popen(temp, shell=True)
        time.sleep(4)
        if ap.poll() is None:
            status = "READY"
    except Exception, ex:
        print ex
        status = "FAIL"
        pid = None
    return status, ap


def close_all_nodes():

    temp = ""

    if platform.system() == "Windows":
        temp = "taskkill /F /IM node.exe"
    if platform.system() == "Linux":
        temp = "killall node"
    subprocess.Popen(temp, shell=True)
    time.sleep(1)



if __name__ == '__main__':

    #temp = get_userid_from_file('HC37VW903116')
    out = update_android_time('ZX1G22B7LM',-1)
    #device_file_operation('HC37VW903116','PUSH', r'E:\AutoTestDemo\TestTasks\apps\420log.apk', '/data/local/tmp/')
    handle_popup_windows(5,'82e2aaad')
    pass



