#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Xuxh'

import os
from time import sleep
#from uiautomator import Device
import threading

from library import uiautomator
from library import device


# def handle_popup_windows(nub,device):

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

def install_app(mydevice,app_path):

    mydevice.app_operation('INSTALL',app_path)
    sleep(2)
    mydevice.app_operation('LAUNCH')
    sleep(2)

def do_popup_windows(nub,uid):

    find_text = [u"安装",u"允许",u"跳过",u"继续",u"开启",u"欢迎"]

    for i in range(nub):
        uiautomator.click_popup_window(uid,find_text)
        myDevice = device.Device(uid)
        myDevice.emulate_swipe_action()


def init_app(uid):

    myDevice = device.Device(uid)
    myDevice.uninstall_app()
    # get path of app
    local_path =os.path.abspath(os.path.join('apps/',myDevice.CONFIG.getValue(uid,'app')))
    mobile_path = myDevice.CONFIG.getValue(uid,'mobile_app_path')
    myDevice.device_file_operation('PUSH',local_path,mobile_path)
    app_path = os.path.join(mobile_path,myDevice.CONFIG.getValue(uid,'app'))

    try:
        threads = []
        install = threading.Thread(target=install_app, args=(myDevice,app_path))
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

    myDevice.app_operation('CLOSE')
    # delete APK file on mobile
    myDevice.device_file_operation('DELETE',app_path,'')


if __name__ == '__main__':

    pass





