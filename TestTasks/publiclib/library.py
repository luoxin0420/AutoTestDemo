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

import configuration
import myglobal



CONFIG = configuration.configuration()
CONFIG.fileConfig(myglobal.CONFIGURATONINI)


def locate_element(driver, locate_string):

    parameters = locate_string.split('--')
    element = None

    try:

        if len(parameters) < 2:
            elements = driver.find_elements_by_id(parameters[0])
        else:
            if parameters[1] == 'CLASS':
                elements = driver.find_elements_by_class_name(parameters[0])
        try:
            if len(elements) < 2:
                element = elements[0]
            elif len(elements) >= int(parameters[2]):
                element = elements[parameters[2]]
        except:
            element = elements[0]
    except Exception,ex:

        print ex

    return element


def locate_elements(driver, locate_string):

    parameters = locate_string.split('--')
    elements = None

    try:

        if len(parameters) < 2:
            elements = driver.find_elements_by_id(parameters[0])
        else:
            if parameters[1] == 'CLASS':
                elements = driver.find_elements_by_class_name(parameters[0])

    except Exception,ex:

        print ex

    return elements


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


def app_operation(uid,action,path=''):

    pkg = CONFIG.getValue(uid,'apppackage')
    activity = CONFIG.getValue(uid,'appactivity')

    pname = ''.join([pkg, '/', activity])

    if pkg != "":
        if action == "LAUNCH":
            cmd = "".join(["adb -s ", uid, " shell am start -n ", pname])
        if action == "CLOSE":
            cmd = "".join(["adb -s ", uid, " shell am force-stop ", pname])
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


def update_android_time(uid):

    interval_num = CONFIG.getValue(uid, 'frequence_num')
    interval_unit = CONFIG.getValue(uid, 'frequence_unit')

    # get android time, then get expected time stamp
    cmd = "".join(["adb -s ", uid, " shell date +%Y%m%d.%H%M%S "])
    out = shellPIPE(cmd).replace('\r\r\n', '')

    cur_time = datetime.datetime.strptime(out,'%Y%m%d.%H%M%S')
    if interval_unit.lower() == 'hour':
        expe_time = cur_time + datetime.timedelta(hours=int(interval_num))
    else:
        expe_time = cur_time + datetime.timedelta(days=int(interval_num))
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
    out1 = out.replace('\r\r\n','')
    m = content.match(out1)
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


def create_logger(device_name):

    cur_date = datetime.datetime.now().strftime("%Y%m%d")
    parent_path = ''.join(["log/", cur_date])
    if not os.path.isdir(parent_path):
        os.mkdir(parent_path)

    now = datetime.datetime.now().strftime("%Y%m%d%H%M")
    filename = ''.join([parent_path, '/', device_name, '_', now, "test.log"])
    logger = logging.getLogger("VlifeTest")
    formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)
    return filename,logger


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
    out = update_android_time('HC37VW903116')
    pass


