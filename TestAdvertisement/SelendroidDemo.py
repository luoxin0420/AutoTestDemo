#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Xuxh'

import argparse
import sys
from time import sleep
import os
import time
import datetime

from library import device
from logger import log
from library import myglobal
from library import desktop
from library import configuration
from library import logcat
from library import pJson

CONFIG = configuration.configuration()
CONFIG.fileConfig(myglobal.CONFIGURATONINI)

def start_service():

    my_device.device_service_operation('STOP')
    sleep(2)
    my_device.device_service_operation('START')

    wtime = CONFIG.getValue('Runtime','waittime')
    sleep(wtime)


def detect_logcat(out):

    data = ''
    result = False

    log = logcat.DumpLogcatFileReader(out,my_device.uid,'com.vlife.mxlock.wallpaper:main','4697956883387773100;query_window_condition_list')
    log.start()
    time.sleep(20)
    log.stop()
    plog = logcat.ParseLogcat(out)
    data = plog.get_complete_jsondata('responseDataJson:')

    if data != '':
        result = True

    return data, result


def download_data(data,logpath):

    temp = pJson.parseJson(data)
    value = temp.extract_element_value('l[0].a.d.fa')
    url = 'http://stage.3gmimo.com/handpet/' + value[0]
    print url

    now = datetime.datetime.now().strftime("%H%M%S")
    parent_path = os.path.join(logpath,now)

    # create multi layer directory
    if not os.path.isdir(parent_path):
        os.makedirs(parent_path)
    download_file = os.path.join(parent_path,'download.zip')
    desktop.download_data(url, download_file)

    desktop.unzip_file(download_file,parent_path)

    return parent_path


def verify_image(fname, data,filepath):

    parent_path = download_data(data,filepath)

    result = True

    return result


def write_html_header(logname,title):

    htmlhead = '''<html>
<head>
<title></title>
<meta http-equiv="Content-Type" content="text/html; charset=gbk">
<style type="text/css">
<!--
table{empty-cells:show;table-layout:fixed;}
#wrap{word-wrap:break-word;overflow:hidden;}
.table_whole {width:320px;}
.table_whole td{background-color:#E0E0E0;}
.table_whole th{background-color:#d0d0d0;}
-->
</style>
<script type="text/javascript">
function resetResultTable()
{
var pass_count = document.getElementsByName("pass").length
var fail_count = document.getElementsByName("fail").length
var error_count = document.getElementsByName("error").length
var all_count = pass_count + fail_count + error_count
document.getElementById('all_count').innerHTML=all_count
document.getElementById('pass_count').innerHTML=pass_count
document.getElementById('fail_count').innerHTML=fail_count
document.getElementById('error_count').innerHTML=error_count
}
</script>
</head>
<body onload="resetResultTable()">
<center><h1>''' + title + '''</h1></center>
<table class="table_whole" border="1">
<tr align="right">
<th>ALL</th>
<th>PASS</th>
<th>FAIL</th>
<th>ERROR</th>
</tr>
<tr align="right">
<td><font color="Black" id="all_count"></font></td>
<td><font color="#007500" id="pass_count"></font></td>
<td><font color="Red" id="fail_count"></font></td>
<td><font color="Red" id="error_count"></font></td>
</tr>
</table>
'''
    tableheader = '''
<br>
<table border="1" width="1000">
<thead bgcolor="#d0d0d0">
<tr>
<th width="15%">TIME</th>
<th width="15%">TAG</th>
<th>MESSAGE</th>
</tr>
</thead>
<tbody id="wrap" bgcolor="#E0E0E0">'''
    with open(logname,'a+') as wfile:

        wfile.write(htmlhead)
        wfile.write(tableheader)


def get_screenshots_name(logname,number):

    dirname = os.path.dirname(os.path.abspath(logname))
    image_path = os.path.join(dirname,'image')

    if not os.path.isdir(image_path):
        os.makedirs(image_path)
    basename = ''.join(['screen',str(number), '.png'])
    filename = os.path.join(image_path,basename)
    return filename

if __name__ == '__main__':

    global my_logger
    global my_device

    newParser = argparse.ArgumentParser()
    newParser.add_argument("-u", "--uid", dest="uid", help="Your device uid")

    args = newParser.parse_args()
    uid = args.uid

    if uid is None:
        sys.exit(0)

    # verify if device is connected
    devices = device.Device.get_connected_devices()
    if uid not in devices:
        print "Device is not connected, please check"
        sys.exit(0)

    my_device = device.Device(uid)
    logname = desktop.get_log_name(uid, 'verify.html')

    # create log
    if not os.path.exists(logname):
        write_html_header(logname, 'Verify Advertisement')
    my_logger = log.Log(logname)

    # start-up service and monitor logcat
    out = os.path.join(os.path.abspath(logname),'out.log')
    fileobj = open(out, 'w+')
    monitor_logcat= logcat.DumpLogcatFileReader(fileobj, my_device.uid, 'com.vlife.mxlock.wallpaper:main','query_window_condition_list;responseDataJson')
    monitor_logcat.start()

    #start_service()

    loop_number = 0
    TestFlag = True
    dtime = CONFIG.getValue('Runtime','duration')

    while TestFlag:

        result, data = detect_logcat(out,dtime)

        if result:
            my_logger.write('TEST_START','Start verify new advertisement')
            fname = get_screenshots_name(logname,loop_number)
            my_device.app_operation('LAUNCH')
            sleep(1)
            my_device.get_device_screenshot(fname)
            temp = '<img src=\"' + fname + '\" width=120 height=200 />'
            my_logger.write('TEST_DEBUG','Actual Screen:'+temp)
            result = verify_image(fname,data,os.path.abspath(logname))
            if result:
                my_logger.write('TEST_PASS','test is passed')
            else:
                my_logger.write('TEST_PASS','test is failed')

            # access to the next cycle
            sleep(dtime)
        else:
            TestFlag = False

        loop_number += 1

    monitor_logcat.stop()