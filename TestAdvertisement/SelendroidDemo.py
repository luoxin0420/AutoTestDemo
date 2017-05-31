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
from library import imagemagick


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

    log = logcat.DumpLogcatFileReader(out,my_device.uid,'com.vlife.mxlock.wallpaper:main','4697956883387773100;query_window_condition_list')
    log.start()
    time.sleep(durtation)
    log.stop()
    #out = r'E:\AutoTestDemo\TestAdvertisement\log\20170523\860BCMK22LD8\201705231654\out.log'
    plog = logcat.ParseLogcat(out)
    data = plog.get_complete_jsondata('responseDataJson:')

    if data != '':
        result = True

    return data, result


def download_data(data,logpath):

    image_file = ''
    layout = ''
    # create download path
    now = datetime.datetime.now().strftime("%H%M%S")
    parent_path = os.path.join(logpath,now)
    # create multi layer directory
    if not os.path.isdir(parent_path):
        os.makedirs(parent_path)

    # get url and download image file
    try:
        jsonData = pJson.parseJson(data)
        link = CONFIG.getValue(my_device.uid,'adv_url')
        value1 = jsonData.extract_element_value(link)
        if len(value1[0]) > 0:
            host = CONFIG.getValue('Common','host')
            url = host + value1[0][0]
            # get file name
            name = value1[0][0].split('/')[-1][:-4]
            image_file = os.path.join(parent_path,name)
            desktop.download_data(url, image_file)

        # get layout file
        link = CONFIG.getValue(my_device.uid,'layout_url')
        value2 = jsonData.extract_element_value(link)
        if len(value2[0]) > 0:
            url = host + value2[0][0]
            name = value2[0][0].split('/')[-1]
            layout = os.path.join(parent_path,name)
            desktop.download_data(url, layout)
    except Exception,ex:

        print ex
        print data

    return image_file,layout


def verify_image(expc_img,actu_img,layout):

    value = False
    try:
        width, height = my_device.get_screen_size()
        dpi = int(CONFIG.getValue(my_device.uid,'dpi'))
        img_height = int(3 * dpi)

        # resize expected image according to actual screen
        exp_name = os.path.join(os.path.dirname(expc_image),'resize.png')
        imagemagick.resize_image(expc_image,width,img_height,exp_name)
        # crop advertisement image from snapshot
        actu_name = os.path.join(os.path.dirname(expc_image),'crop.png')
        imagemagick.crop_image(actu_image,width,img_height,0,0,actu_name)

        # crop a small 30x30 image from the center of image
        eimg = os.path.join(os.path.abspath(os.path.dirname(expc_image)),'eimg.png')
        aimg = os.path.join(os.path.abspath(os.path.dirname(expc_image)),'aimg.png')

        imagemagick.crop_image(actu_name,30,30,int(width/2),int(img_height/2),aimg)
        imagemagick.crop_image(exp_name,30,30,int(width/2),int(img_height/2),eimg)

        # write log
        temp = '<img src=\"' + eimg + '\" width=50 height=50 />'
        my_logger.write('TEST_DEBUG','Expected Image:' + temp)
        temp = '<img src=\"' + aimg + '\" width=50 height=50 />'
        my_logger.write('TEST_DEBUG','Actual Image:' + temp)

        # compare image
        value = imagemagick.compare_image(aimg,eimg)

    except Exception,ex:

        print ex

    return value


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
    dtime = 300

    # start-up service and monitor logcat
    logpath = os.path.dirname(logname)
    out = os.path.abspath(os.path.join(logpath,'out.log'))

    while TestFlag:

        my_logger.write('TEST_START','Start verifying advertisement ' + 'number:' + str(loop_number))
        data, result = detect_logcat(out,dtime)
        my_logger.write('TEST_DEBUG','Dump Window Data:' + data)
        expc_image,layout = download_data(data, logpath)

        if result and expc_image != '':
            temp = '<img src=\"' + os.path.abspath(expc_image) + '\" width=120 height=200 />'
            my_logger.write('TEST_DEBUG','Expected Image:' + temp)

            # get actual screenshots
            actu_image = get_screenshots_name(logname,loop_number)
            my_device.app_operation('LAUNCH')
            # add sleep time
            sleep(4)
            my_device.get_device_screenshot(actu_image)
            temp = '<img src=\"' + actu_image + '\" width=120 height=200 />'
            my_logger.write('TEST_DEBUG','Actual Screen:'+ temp)
            my_device.app_operation('CLOSE')
            result = verify_image(expc_image,actu_image,layout)

            if result:
                my_logger.write('TEST_PASS','test is passed')
            else:
                my_logger.write('TEST_FAIL','test is failed')
        else:
            my_logger.write('TEST_FAIL','There is no response window data')

        loop_number += 1

        if loop_number == 5:
            TestFlag = False

        # access to the next cycle
        sleep(10)


