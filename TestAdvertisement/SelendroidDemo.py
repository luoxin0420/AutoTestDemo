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
from library import desktop
from library import configuration
from library import logcat
from library import pJson
from library import myglobal


CONFIG = configuration.configuration()
print os.path.abspath(myglobal.CONFIGURATONINI)
CONFIG.fileConfig(myglobal.CONFIGURATONINI)


def start_service():

    my_device.device_service_operation('STOP')
    sleep(2)
    my_device.device_service_operation('START')

    wtime = CONFIG.getValue('Runtime','waittime')
    sleep(wtime)


def detect_logcat(out,durtation):

    data = ''
    result = False

    # log = logcat.DumpLogcatFileReader(out,my_device.uid,'com.vlife.mxlock.wallpaper:main','4697956883387773100;query_window_condition_list')
    # log.start()
    # time.sleep(durtation)
    # log.stop()
    out = r'E:\AutoTestDemo\TestAdvertisement\log\20170519\860BCMK22LD8\201705191542\out.log'
    plog = logcat.ParseLogcat(out)
    data = plog.get_complete_jsondata('responseDataJson:')

    if data != '':
        result = True

    return data, result


def download_data(data,logpath):

    # create download path
    now = datetime.datetime.now().strftime("%H%M%S")
    parent_path = os.path.join(logpath,now)
    # create multi layer directory
    if not os.path.isdir(parent_path):
        os.makedirs(parent_path)

    # get url and download image file
    jsonData = pJson.parseJson(data)
    link = CONFIG.getValue(my_device.uid,'adv_url')
    value = jsonData.extract_element_value(link)
    host = CONFIG.getValue('Common','host')
    url = host + value[0][0]
    # get file name
    name = value[0][0].split('/')[-1][:-4]
    image_file = os.path.join(parent_path,name)
    desktop.download_data(url, image_file)

    # get layout file
    link = CONFIG.getValue(my_device.uid,'layout_url')
    value = jsonData.extract_element_value(link)
    url = host + value[0][0]
    name = value[0][0].split('/')[-1]
    layout = os.path.join(parent_path,name)
    desktop.download_data(url, layout)

    return image_file,layout


def verify_image(expc_img,actu_img,layout):

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

    # create test log
    if not os.path.exists(logname):
        write_html_header(logname, 'Verify Advertisement')
    my_logger = log.Log(logname)


    #start_service()

    loop_number = 0
    TestFlag = True
    dtime = CONFIG.getValue('Common','duration')
    dtime = int(dtime) * 60

    # start-up service and monitor logcat
    logpath = os.path.dirname(logname)
    out = os.path.join(logpath,'out.log')

    while TestFlag:

        my_logger.write('TEST_START','Start verifying advertisement ' + 'number:' + str(loop_number))
        data, result = detect_logcat(out,dtime)
        my_logger.write('TEST_DEBUG','Dump Window Data:' + data)
        if result:
            expc_image,layout = download_data(data, logpath)
            temp = '<img src=\"' + os.path.abspath(expc_image) + '\" width=120 height=200 />'
            my_logger.write('TEST_DEBUG','Expected Image:' + temp)

            # get actual screenshots
            actu_image = get_screenshots_name(logname,loop_number)
            my_device.app_operation('LAUNCH')
            sleep(1)
            my_device.get_device_screenshot(actu_image)
            temp = '<img src=\"' + actu_image + '\" width=120 height=200 />'
            my_logger.write('TEST_DEBUG','Actual Screen:'+ temp)
            result = verify_image(expc_image,actu_image,layout)

            if result:
                my_logger.write('TEST_PASS','test is passed')
            else:
                my_logger.write('TEST_FAIL','test is failed')

            # access to the next cycle
            sleep(dtime)
        else:
            TestFlag = False
            my_logger.write('TEST_FAIL','There is no response window data')

        loop_number += 1


