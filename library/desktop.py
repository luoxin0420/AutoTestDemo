#! /usr/bin/python
# -*- coding: utf-8 -*-
import urllib2

__author__ = 'Xuxh'

import os
import sys
import logging
import time
import datetime
import subprocess
import smtplib
import psutil
import signal
from email import Encoders
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
import platform
import zipfile

import configuration
import myglobal

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


def get_desktop_os_type():

    return platform.system()


def kill_child_processes(parent_pid, sig=signal.SIGTERM):

    try:
        p = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    child_pid = p.children(recursive=True)

    for pid in child_pid:
        os.kill(pid.pid, sig)


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


def get_log_name(device_name,basename):

    cur_date = datetime.datetime.now().strftime("%Y%m%d")
    now = datetime.datetime.now().strftime("%Y%m%d%H%M")
    parent_path = os.path.join('log',cur_date,device_name,now)

    # create multi layer directory
    if not os.path.isdir(parent_path):
        os.makedirs(parent_path)

    filename = os.path.join(parent_path,basename)

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


def download_data(url, fname):

    f = urllib2.urlopen(url)
    data = f.read()
    with open(fname, "wb") as wfile:
        wfile.write(data)


def remove_sufix_name(full_name):

    fname = os.path.basename(full_name)
    dirpath = os.path.dirname(full_name)

    if os.path.splitext(fname)[1] == '.pet':
        newname = fname.split('.')[:-2]
        newfile = os.path.join(dirpath,newname)
        os.rename(full_name,newfile)


def unzip_file(fname,despath):

    zfile = zipfile.ZipFile(fname,'r')

    for f in zfile.namelist():
        if f.endswith('/'):
            os.makedirs(f)
        else:
            zfile.extract(f,despath)

if __name__ == '__main__':

    pass



