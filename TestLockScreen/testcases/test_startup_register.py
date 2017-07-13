#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Xuxh'


import os
import sys
#sys.path.append(r"E:\AutoTestDemo")
#reload(sys)
# print sys.path
import re
try:
    import unittest2 as unittest
except(ImportError):
    import unittest
from time import sleep
from library import configuration
from library import logcat as dumplog
from library import device
from library import desktop
from library import pXml
from library import uiautomator
from library import desktop
from library import newTestSuite
from library import HTMLTestRunner
import threading


PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)

# ########以下用例测试前提条件#########
# 手机上需要有SIM卡
# 手机上需要有SDCARD
# 需要准备相应的安装包及第三包安装包，并在配置文件中指定源路径及目标路径
# 手机的语言设置请设成中文
# 需要设置手机锁屏,解锁方式最好是上滑屏与向右滑屏
# 确保第三方应用并没有在待测手机上安装
# 保证手机在第一次运行是解锁状态，使用的主题是系统主题
# 日期设置成自动，自动锁屏设置到30分钟


class TestStartupRegister(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        self.master_service = CONFIG.getValue(DEVICENAME,'master_service')
        self.slave_service = CONFIG.getValue(DEVICENAME,'slave_service')
        self.slave_main_process = self.slave_service + ':main'
        self.omit_cases = CONFIG.getValue(DEVICENAME, 'omit_cases')
        self.set_theme = bool(CONFIG.getValue(DEVICENAME, 'set_theme'))
        self.set_theme_pkg = CONFIG.getValue(DEVICENAME, 'set_theme_pkg')

    def setUp(self):

        self.log_name = None
        self.log_path = None
        self.log_reader = None
        self.result = False
        self.reg_uid = ''
        self.filter_result = {}
        self.log_count = 1
        self.double_process = False
        self.pid_uid = {}

        for title in self.omit_cases.split(':'):

            if self._testMethodName.find(title) != -1:
                self.skipTest('this case is not supported by this version')

    def tearDown(self):

        #self._outcomeForDoCleanups = result   # Python 3.2, 3.3
        try:
                # newname = self._testMethodName +'fail'+ '.txt'
                # newname = os.path.join(os.path.dirname(self.log_name),newname)
                # os.rename(self.log_name,newname)
                if hasattr(self, '_outcome'):  # Python 3.4+
                    result = self.defaultTestResult()  # these 2 methods have no side effects
                    self._feedErrorsToResult(result, self._outcome.errors)
                else:  # Python 3.2 - 3.3 or 2.7
                    result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
                error = self.list2reason(result.errors)
                failure = self.list2reason(result.failures)
                ok = not error and not failure

                if LOOP_NUM == 0:
                    RESULT_DICT.setdefault(self._testMethodName, {})['Result'] = []
                    RESULT_DICT.setdefault(self._testMethodName, {})['Log'] = []

                if ok:
                    RESULT_DICT[self._testMethodName]['Result'].append('PASS')
                    RESULT_DICT[self._testMethodName]['Log'].append('')
                else:
                    RESULT_DICT[self._testMethodName]['Result'].append('FAILED')
                    RESULT_DICT[self._testMethodName]['Log'].append(os.path.basename(self.log_name))
                    # insert into fail case list
                    FAIL_CASE.append(self._testMethodName)
                    
        except Exception,ex:
                print ex

        # make mobile theme to system theme
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'system')
        # close all adb to avoid 5037 port occupation
        desktop.close_all_program('adb')
        # restart adb server
        sleep(1)
        DEVICE.restart_adb_server()
        sleep(10)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    def dump_log_start(self, service,filter_condition):

        name = ''.join([self._testMethodName, '_', str(LOOP_NUM), '_', str(self.log_count)])
        self.log_name = os.path.join(LogPath,name)
        self.log_count += 1
        self.log_reader = dumplog.DumpLogcatFileReader(self.log_name,DEVICENAME,service,filter_condition)
        self.log_reader.clear_logcat()
        self.log_reader.start()

    def dump_log_stop(self):

        self.log_reader.stop()

    def get_pid(self):

        pid_list = []
        try:
            for name in (self.slave_main_process,self.master_service):
                pid = dumplog.DumpLogcatFileReader.get_PID(DEVICENAME,name)
                if str(pid) > 0:
                    pid[0] = pid[0].strip()
                    pid_list.append(pid[0])
        except Exception,ex:
            print ex
            return []

        return pid_list

    def verify_register_uid(self, log):

        pid1 = ''
        uid1 = ''
        result = False
        #print log
        for ln in log:
            if pid1 == '' or uid1 == '':
                pid1, uid1 = ln.split(':')
                self.pid_uid[pid1] = uid1
                print 'The firstly find pid:' + str(pid1)
                print 'The firstly find uid:' + str(uid1)
            else:
                pid, uid = ln.split(':')
                if pid != pid1:
                    self.pid_uid[pid] = uid
                    if uid != uid1:
                        result = True
                    else:
                        result = False
                        print 'uid should not same for different process'
                    print 'The secondly find pid:' + str(pid)
                    print 'The secondly find uid:' + str(uid)
                else:
                    continue
        return result

    def verify_wallpaper_lockscreen_id(self,lsid,wpid):

        result = True
        build_type = CONFIG.getValue(DEVICENAME,'build_type')

        print 'Actual lockscreen_id:' + lsid
        print 'Actual wallpaper_id:' + wpid

        lsid = int(lsid)
        wpid = int(wpid)

        if build_type.upper() == 'MAGAZINE':
            if lsid !=0 or wpid !=0:
                print 'id value is not right, expected value is 0'
                result = False

        if build_type.upper() == 'THEMELOCK':
            if lsid ==0 or wpid !=0:
                print 'Excepted lockscreen_id is not 0'
                print 'Excepted wallpaper_id is 0'
                result = False

        if build_type.upper() == 'WALLPAPER':
            if lsid !=0 or wpid ==0:
                print 'Excepted lockscreen_id is  0'
                print 'Excepted wallpaper_id is not 0'
                result = False

        if build_type.upper() == 'WALLPAPER_THEMELOCK':
            if lsid ==0 or wpid ==0:
                print 'Excepted lockscreen_id is not 0'
                print 'Excepted wallpaper_id is not 0'
                result = False

        return result

    # verify content of login package
    def verify_pkg_content(self,contents):

        result = True
        verify_node = ['uid','lockscreen_id','wallpaper_id','imei','mac','platform','product','product_soft','promotion']
        #verify_node = ['uid','lockscreen_id','wallpaper_id','imei','mac','platform','product','promotion']
        find_node = []
        for cont in contents:

            data = pXml.parseXml(cont)
            for name in verify_node:
                try:
                    if name != 'platform' and name != 'product_soft':
                        value = data.get_elements_text(name)[0]
                    elif name == 'platform':
                        value = data.get_elements_attribute_value(name,'version')[0]
                    else:
                        value = data.get_elements_attribute_value(name,'soft')[0]
                    self.filter_result[name] = value
                    find_node.append(name)
                except Exception,ex:
                        continue

        # verify if node not found
        diff_node = list(set(verify_node).difference(set(find_node)))
        for name in diff_node:
            print name + ' node is not found '
            result = False

        # verify wallpaper/lockscreen_id according to different product
        try:
            lsid = self.filter_result['lockscreen_id']
            wpid = self.filter_result['wallpaper_id']
            result = self.verify_wallpaper_lockscreen_id(lsid,wpid)
            print 'wallpaper/lockscreen_id value is right'
        except Exception,ex:
            result = False
            print 'wallpaper/lockscreen_id value is not right'

        # start to verify detailed content
        for key, value in self.filter_result.items():

            flag = False
            if key == 'lockscreen_id' or key == 'wallpaper_id':
                continue
            else:
                print key + ': actual value is ' + str(value)
                if key == 'mac':
                    exp_mac = DEVICE.get_device_mac_address()
                    print 'Expected mac address:' + str(exp_mac)
                    if exp_mac.upper().strip() != value.strip():
                        result = False
                        flag = True
                if key == 'imei':
                    exp_imei = DEVICE.get_IMEI()
                    print 'Expected IMEI:' + str(exp_imei)
                    if str(exp_imei) != str(value):
                        result = False
                        flag = True
                if key == 'platform':
                    exp_ver = DEVICE.get_os_version()
                    print 'Expected Android Version:' + str(exp_ver)
                    if exp_ver != int(value.split('.')[0]):
                        result = False
                        flag = True
            if flag:
                print key + ': value is not right'

        return result

    def filter_log_result(self,action='activation',findstr='Start proc'):

        result = False
        pid = self.get_pid()
        #pid = ['1139','1794']
        login_pkg = []
        register_pkg = []
        with open(self.log_name) as reader:
            for line in reader:
                # remove redundance space
                line = ' '.join(filter(lambda x: x, line.split(' ')))
                values = line.split(' ')
                # values[6:] is text column
                try:
                    text = ' '.join(values[6:])
                    # 验证激活的日志,查找'Start proc’
                    if action == 'activation':
                        if text.find(self.slave_main_process) != -1 and text.startswith(findstr):
                            result = True
                            print 'Find log:' + line
                            break

                    # 验证注册的日志,查找key:uid 并得到value
                    if action == "register":
                        if values[2] in pid and text.find(findstr) != -1:
                            temp = text.split('key:uid,value:')
                            if len(temp) > 1:
                                if temp[1].strip() != 'null':
                                    if not self.double_process:
                                        result = True
                                        self.reg_uid = temp[1]
                                        print 'Find log:' + line
                                        break
                                    else:
                                        # pid:uid
                                        pid_uid = ':'.join([str(values[2]),temp[1].strip()])
                                        if pid_uid not in register_pkg:
                                            register_pkg.append(pid_uid)
                                        else:
                                            continue

                    # 过滤登录包的日志
                    if action == "login":
                        if values[2] in pid:
                            for ft in findstr.split(';'):
                                if text.find(ft) != -1:
                                    keyword =r'.*(<query.*/query>).*'
                                    content = re.compile(keyword)
                                    m = content.match(text)
                                    if m:
                                        pid_pkg = ':::'.join(([str(values[2]),m.group(1)]))
                                        login_pkg.append(pid_pkg)
                except Exception, ex:
                    print ex
                    continue

        # 验证双进程注册日志
        if len(register_pkg) > 0 and action == "register":
            result = self.verify_register_uid(register_pkg)

        # 验证登录包内容
        if len(login_pkg) > 0 and action == "login":
            for p in pid:
                contents = []
                for lp in login_pkg:
                    vpid = lp.split(':::')
                    if vpid[0] == p:
                        contents.append(vpid[1])
                print 'Verify login package content,current PID:' + str(p)
                result = self.verify_pkg_content(contents)
                if not result:
                    break

        return result

    def unlock_screen(self):

        DEVICE.screen_on_off("OFF")
        sleep(2)
        DEVICE.screen_on_off("ON")
        sleep(2)
        DEVICE.emulate_swipe_action()
        sleep(1)

    def reboot_device(self):

        DEVICE.device_reboot()
        sleep(10)

        # monitor logcat
        self.dump_log_start(self.master_service, '')
        sleep(15)
        # unlock screen
        self.unlock_screen()
        sleep(25)
        self.dump_log_stop()
        self.result = self.filter_log_result()

    def change_wifi(self):

        # close wifi, monitor logcat
        self.unlock_screen()
        self.dump_log_start(self.master_service, '')
        DEVICE.wifi_operation('OFF')
        sleep(50)
        self.dump_log_stop()
        self.result = self.filter_log_result()
        #recovery wifi connection
        DEVICE.wifi_operation('ON')
        sleep(5)

    def close_app(self):

        DEVICE.app_operation('CLOSE', service=self.slave_service)
        sleep(5)

    def clear_app(self):

        DEVICE.app_operation('CLEAR', service=self.slave_service)
        DEVICE.app_operation('CLEAR', service='com.android.systemui')
        sleep(5)

    def sdcard_action(self,action):

        self.close_app()
        self.dump_log_start(self.master_service,'')
        DEVICE.sdcard_operation(action)
        sleep(10)
        self.dump_log_stop()
        self.result = self.filter_log_result()

    #测试自激活
    #重启手机,第一次启动
    def test_activation_100_first_startup(self):

        #clear app
        self.clear_app()
        self.reboot_device()
        self.assertEqual(True,self.result)

    #重启手机,非第一次启动
    def test_activation_101_startup(self):

        #close app
        self.close_app()
        self.reboot_device()
        print self.result
        self.assertEqual(True,self.result)

    #切换WIFI,非首次启动
    def test_activation_103_wifi_change(self):

        self.close_app()
        self.change_wifi()
        self.assertEqual(True,self.result)

    #切换WIFI，首次启动
    def test_activation_104_first_wifi_change(self):

        self.clear_app()
        self.change_wifi()
        self.assertEqual(True,self.result)

    def install_thirdapp(self,action):

        self.dump_log_start(self.master_service,'')
        app_path = PATH(PATH('../ext/' + 'advhelp.apk'))
        DEVICE.install_app_from_desktop(action,app_path)
        sleep(25)
        self.result = self.filter_log_result()

    def install_app(self):

        self.close_app()
        # install the third party of app
        self.install_thirdapp('INSTALL')
        sleep(2)
        DEVICE.app_operation('UNINSTALL',service='com.vlife.qateam.advhelp')
        sleep(2)

    def cover_install_app(self):

        self.close_app()
        print 'Install the third of party application'
        self.install_thirdapp('INSTALL')
        sleep(2)
        print 'close main process'
        self.close_app()
        sleep(2)
        print 'Cover install the third of party application'
        self.install_thirdapp('COVER_INSTALL')
        DEVICE.app_operation('UNINSTALL',service='com.vlife.qateam.advhelp')
        sleep(2)

    def install_app_with_pop_window(self,install_type):

        find_text = [u"安装", u"允许"]
        try:
            threads = []
            if install_type.upper() == 'FIRST_INSTALL':
                install = threading.Thread(target=self.install_app)
            else:
                install = threading.Thread(target=self.cover_install_app)
            proc_process = threading.Thread(target=DEVICE.do_popup_windows, args=(5, find_text))
            threads.append(proc_process)
            threads.append(install)
            for t in threads:
                t.setDaemon(True)
                t.start()
                sleep(3)
            t.join()
        except Exception, ex:
             print ex

    #第一次安装第三方APP
    def test_activation_105_first_install_thirdapp(self):

        self.install_app_with_pop_window('first_install')
        self.assertEqual(True,self.result)


    #非第一次安装第三方APP
    def test_activation_106_cover_install_thirdapp(self):

        self.install_app_with_pop_window('cover_install')
        self.assertEqual(True,self.result)

    #更新手机时间，满足三小时时间间隔
    def test_activation_107_update_time_active(self):

        self.close_app()
        self.unlock_screen()
        self.dump_log_start(self.master_service,'')
        # update time and make screen on/off
        DEVICE.update_android_time(3)
        sleep(5)
        DEVICE.screen_on_off("OFF")
        sleep(10)
        DEVICE.screen_on_off("ON")
        sleep(10)
        self.dump_log_stop()
        self.result = self.filter_log_result()
        self.assertEqual(True,self.result)

    # #拔SD卡
    # def test_activation_108_umount_sdcard(self):
    #
    #     self.sdcard_action("UMOUNT")
    #     self.assertEqual(True,self.result)
    #
    # #插SD卡
    # def test_activation_109_mount_sdcard(self):
    #
    #     self.sdcard_action("MOUNT")
    #     self.assertEqual(True,self.result)


    #资源管理器杀掉主进程，满足三小时时间间隔
    def test_activation_110_update_time_killbythird(self):

        # unlock screen
        self.unlock_screen()
        # 通过多任务列表关闭所有应用
        DEVICE.send_keyevent('KEYCODE_APP_SWITCH')
        sleep(2)
        try:
            element = uiautomator.Element(DEVICENAME)
            event = uiautomator.Event(DEVICENAME)
            ele = element.findElementByName(u'全部清除')
            if ele is not None:
                event.touch(ele[0], ele[1])
                sleep(2)
            else:
                for i in range(20):
                    DEVICE.send_keyevent('KEYCODE_DPAD_DOWN')
                    DEVICE.send_keyevent('KEYCODE_DEL')
                DEVICE.send_keyevent('KEYCODE_HOME')
        except Exception,ex:
            print ex
        if self.get_pid() == 0:
            print 'main process is killed successfully'
            self.assertEqual(0,0)
        else:
            print 'main process is not killed'
            self.assertEqual(0,1)

        # Start monitor log
        # self.dump_log_start(self.master_service,'')
        # # update time and make screen on/off
        # DEVICE.update_android_time(3)
        # sleep(10)
        # DEVICE.screen_on_off("OFF")
        # sleep(2)
        # DEVICE.screen_on_off("ON")
        # self.dump_log_stop()
        # self.result = self.filter_log_result()
        # self.assertEqual(True,self.result)

    def set_device_theme(self, activity_name, theme_type):

        # log in theme app like i theme
        DEVICE.app_operation(action='LAUNCH',service=activity_name)
        sleep(2)
        if theme_type.upper()== 'VLIFE':
            vlife_theme_path = CONFIG.getValue(DEVICENAME,'vlife_theme_path').split(',')
        else:
            vlife_theme_path = CONFIG.getValue(DEVICENAME,'system_theme_path').split(',')
        element = uiautomator.Element(DEVICENAME)
        event = uiautomator.Event(DEVICENAME)

        for text in vlife_theme_path:
            x = 0
            y = 0
            if text.find(':') == -1:
                value = unicode(text)
            # 因为一些点击文字没有响应，需要点击周边的元素
            else:
                value = unicode(text.split(':')[0])
                x = text.split(':')[1]
                y = text.split(':')[2]
            ele = element.findElementByName(value)
            if ele is not None:
                event.touch(ele[0]-int(x), ele[1]-int(y))
                sleep(2)
        # return to HOME
        DEVICE.send_keyevent(3)

    def first_register(self):

        self.clear_app()
        DEVICE.device_reboot()
        # need to wait main process startup
        sleep(25)
        self.unlock_screen()
        sleep(5)
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        # monitor logcat
        self.monitor_logcat(60,'register','key:uid')
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'system')
        self.assertEqual(True,self.result)
        uid = self.reg_uid
        self.reg_uid = ''

        return uid

    def monitor_logcat(self,sleep_time,act,ftr):

        # monitor logcat
        if self.double_process:
            self.dump_log_start(self.master_service, '')
        else:
            self.dump_log_start(self.slave_main_process, '')
        sleep(sleep_time)
        self.dump_log_stop()
        self.result = self.filter_log_result(action=act, findstr=ftr)

    # 测试注册过程
    # 第一次注册，然后清缓存，再次注册，生成不同的uid
    def test_register_200_diff_uid_clearCache(self):

        #DEVICE.app_operation('LAUNCH',service=self.slave_service)
        # first register and get uid
        first_uid = self.first_register()
        # clear and startup main process
        second_uid = self.first_register()
        self.assertNotEqual(first_uid,second_uid)

    # 第一次注册，然后重启，再次注册，生成相同的uid
    def test_register_201_same_uid_reboot(self):

        first_uid = self.first_register()
        # reboot device
        DEVICE.device_reboot()
        sleep(20)
        self.unlock_screen()
        sleep(5)
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        self.monitor_logcat(60,'register','key:uid')
        second_uid = self.reg_uid
        self.assertEqual(first_uid,second_uid)

    # 第一次注册，然后杀掉进程重启，再次注册，生成相同的uid
    def test_register_202_same_uid_killprocessReboot(self):

        first_uid = self.first_register()
        # kill process and reboot device
        self.close_app()
        DEVICE.device_reboot()
        sleep(25)
        self.unlock_screen()
        sleep(5)
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        self.monitor_logcat(60,'register','key:uid')
        second_uid = self.reg_uid
        self.assertEqual(first_uid,second_uid)

    #第一次注册，更新时间到六小时后，然后更新WIFI状态，生成相同的uid
    def test_register_203_same_uid_updateTimeWifi(self):

        first_uid = self.first_register()
        self.log_reader = None
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        # update time
        DEVICE.update_android_time(6)
        # close wifi, then open
        sleep(5)
        DEVICE.wifi_operation('OFF')
        sleep(10)
        DEVICE.wifi_operation('ON')
        sleep(10)
        self.monitor_logcat(60,'register','key:uid')
        second_uid = self.reg_uid
        self.assertEqual(first_uid,second_uid)

    #第一次注册GPRS
    def test_register_204_register_byGPRS(self):

        # close wifi
        DEVICE.wifi_operation('OFF')
        sleep(5)
        DEVICE.gprs_operation('ON')
        sleep(5)
        self.first_register()
        sleep(5)
        DEVICE.wifi_operation('ON')
        sleep(5)
        self.assertEqual(True,self.result)

    # 第一次注册失败在断网情况下，重新联网注册成功
    def test_register_205_Reregister_RecoveryConnect(self):

        print 'WIFI connection disconnected, then reboot device'
        DEVICE.wifi_operation('OFF')
        sleep(5)
        DEVICE.gprs_operation('OFF')
        sleep(3)
        self.close_app()
        DEVICE.device_reboot()
        sleep(20)
        self.unlock_screen()
        sleep(8)
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        self.monitor_logcat(60,'register','key:uid')
        # verify uid is not found
        self.assertEqual(False,self.result)
        self.log_reader = None
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'system')

        # reconnect network
        print 'WIFI connected, then reboot device'
        DEVICE.gprs_operation('ON')
        sleep(5)
        DEVICE.wifi_operation('ON')
        sleep(5)
        DEVICE.device_reboot()
        sleep(20)
        self.unlock_screen()
        sleep(8)
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        self.monitor_logcat(60,'register','key:uid')

        # verify uid is found
        self.assertEqual(True,self.result)

    def double_process_first_register(self):

        # first register and get uid
        self.double_process = True
        self.first_register()
        self.assertEqual(2,len(self.pid_uid))
        prev_pid_uid = self.pid_uid
        self.pid_uid = {}

        return prev_pid_uid

    def double_process_uidsame_compare(self,prev_dict,cur_dict):

        result = True
        if len(prev_dict) == len(cur_dict):
            for v in prev_dict.values():
                if v in cur_dict.values():
                    continue
                else:
                    result = False
        return result

    def test_register_doubleproc_206_diff_uid_clearCache(self):

        result = True
        # first register and get uid
        prev_pid_uid = self.double_process_first_register()
        # self.double_process = True
        # self.first_register()
        # #self.log_name = r'E:\AutoTestDemo\TestLockScreen\log\20170705\ZX1G22TG4F_Nesux6\1555TestStartupRegister\test_206_doubleproc_diff_uid_clearCache_1'
        # #self.result = self.filter_log_result(action='register',findstr='key:uid')
        # self.assertEqual(2,len(self.pid_uid))
        # prev_pid_uid = self.pid_uid
        # self.pid_uid = {}

        # clear and startup main process
        print 'clear and reboot device again, complete new register'
        self.first_register()
        self.assertEqual(2,len(self.pid_uid))
        if len(prev_pid_uid) == len(self.pid_uid):
            for v in prev_pid_uid.values():
                if v not in self.pid_uid.values():
                    continue
                else:
                    result = False
        self.assertEqual(True,result)

    # 第一次注册，然后重启，再次注册，生成相同的uid
    def test_register_doubleproc_207_same_uid_reboot(self):

        # first register and get uid
        prev_pid_uid = self.double_process_first_register()

        # reboot device
        print 'only reboot device, expected uid is same'
        DEVICE.device_reboot()
        sleep(25)
        self.unlock_screen()
        sleep(5)
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        self.monitor_logcat(60,'register','key:uid')

        # Verify if get two uid
        self.assertEqual(2,len(self.pid_uid))
        # Verify uid is same twice for different process
        result = self.double_process_uidsame_compare(prev_pid_uid,self.pid_uid)
        self.assertEqual(True,result)

    #第一次注册，然后杀掉进程重启，再次注册，生成相同的uid
    def test_register_doubleproc_208_uid_killprocReboot(self):

        # first register and get uid
        prev_pid_uid = self.double_process_first_register()

        # kill process and reboot device
        print 'Kill process and reboot device, expected uid is same'
        self.close_app()
        DEVICE.device_reboot()
        sleep(25)
        self.unlock_screen()
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        self.monitor_logcat(60,'register','key:uid')

        # Verify if get two uid
        self.assertEqual(2,len(self.pid_uid))
        # Verify uid is same twice for different process
        result = self.double_process_uidsame_compare(prev_pid_uid,self.pid_uid)
        self.assertEqual(True,result)

    # 第一次注册，更新时间到六小时后，然后更新WIFI状态，生成相同的uid
    def test_register_doubleproc_209_same_uid_updateTimeWifi(self):

        # first register and get uid
        prev_pid_uid = self.double_process_first_register()

        # update time
        print 'Update time and switch WIFI, expected uid is same'
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        DEVICE.update_android_time(6)
        # close wifi, then open
        sleep(5)
        DEVICE.wifi_operation('OFF')
        sleep(10)
        DEVICE.wifi_operation('ON')
        sleep(10)
        self.monitor_logcat(60,'register','key:uid')

        # Verify if get two uid
        self.assertEqual(2,len(self.pid_uid))
        # Verify uid is same twice for different process
        result = self.double_process_uidsame_compare(prev_pid_uid,self.pid_uid)
        self.assertEqual(True,result)

    # Verify package of login
    def test_300_login_pkg_content(self):

        self.first_register()
        self.result = self.filter_log_result('login', 'jabber:iq:auth; jabber:iq:userinfo')
        self.assertEqual(True,self.result)

    #log in multiple times, pkg content is same
    def test_301_pkgsame_multiple_login(self):

        prev_filter_result = {}

        # login multiple times, then verify pkg content
        for i in range(2):
            self.first_register()
            self.result = self.filter_log_result('login','jabber:iq:auth;jabber:iq:userinfo')

            if len(prev_filter_result) > 0:
                try:
                    # delete uid key-value
                    print prev_filter_result
                    print self.filter_result
                    prev_uid = prev_filter_result['uid']
                    print 'previous_uid:' + prev_uid
                    curr_uid = self.filter_result['uid']
                    print 'current_uid:' + curr_uid
                    if prev_uid == curr_uid:
                        print 'uid is same after clear cache'
                except Exception,ex:
                    print 'uid is not found'
                d1 = self.filter_result
                d2 = prev_filter_result
                d1.pop('uid')
                d2.pop('uid')
                self.assertEqual(d1, d2)
            prev_filter_result = self.filter_result
            self.filter_result = {}

    def test_302_relogin_in_5min(self):

        self.first_register()
        self.result = self.filter_log_result('login','jabber:iq:auth;jabber:iq:userinfo')
        self.assertEqual(True,self.result)
        self.log_reader = None
        # wait for 5 minutes, make server session overdue
        sleep(5*60)
        # # 进程重启后触发定期联网,更新时间到到六小时后，会发送登录包
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        DEVICE.update_android_time(6)
        sleep(5)
        # close wifi, then open
        DEVICE.wifi_operation('OFF')
        sleep(5)
        DEVICE.wifi_operation('ON')
        sleep(5)
        self.monitor_logcat(60,'login','jabber:iq:auth;jabber:iq:userinfo')
        self.assertEqual(True,self.result)

    def test_303_relogin_in_1min(self):

        self.clear_app()
        DEVICE.device_reboot()
        # need to wait main process startup
        sleep(25)
        self.unlock_screen()
        sleep(5)
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        # monitor logcat
        self.monitor_logcat(60,'register','key:uid')
        self.result = self.filter_log_result('login','jabber:iq:auth;jabber:iq:userinfo')
        self.assertEqual(True,self.result)
        self.log_reader = None

        # 进程重启后触发定期联网,在一分钟内不会发登录包
        DEVICE.update_android_time(6)
        sleep(2)
        # lighten screen
        DEVICE.screen_on_off('OFF')
        sleep(1)
        DEVICE.screen_on_off('ON')
        sleep(1)
        self.monitor_logcat(60,'login','jabber:iq:auth;jabber:iq:userinfo')
        self.assertEqual(False,self.result)

    def test_304_relogin_in_1minReboot(self):

        self.first_register()
        self.result = self.filter_log_result('login','jabber:iq:auth;jabber:iq:userinfo')
        self.assertEqual(True,self.result)
        prev_uid = self.filter_result.pop('uid')
        self.filter_result = {}
        self.log_reader = None
        # # 进程重启后触发定期联网,发登录包
        DEVICE.device_reboot()
        sleep(25)
        self.unlock_screen()
        sleep(8)
        if self.set_theme:
            self.set_device_theme(self.set_theme_pkg, 'vlife')
        self.monitor_logcat(60,'login','jabber:iq:auth;jabber:iq:userinfo')
        self.assertEqual(True,self.result)
        curr_uid = self.filter_result.pop('uid')
        self.assertEqual(prev_uid,curr_uid)

    def test_login_doubleproc_306_check_pkg(self):

        self.double_process_first_register()
        self.result = self.filter_log_result('login','jabber:iq:auth;jabber:iq:userinfo')
        self.assertEqual(True,self.result)


def init_env():

    #copy files to device
    lock_screen = CONFIG.getValue(DEVICENAME,'vlife_start_lockscreen')
    file_list = CONFIG.getValue(DEVICENAME,'pushfile').split(';')
    # try:
    #     for fname in file_list:
    #         orgi,dest = fname.split(':')
    #         orgi = PATH('../ext/' + orgi)
    #         if os.path.isfile(orgi):
    #             DEVICE.device_file_operation('push',orgi,dest)
    # except Exception, ex:
    #     print ex
    #     print ex)
    #     print "initial environment is failed")
    #     sys.exit(0)


def run(dname,loop=1):

    global DEVICENAME, CONFIG, DEVICE,LogPath
    global LOOP_NUM, RESULT_DICT, FAIL_CASE
    
    CONFIG = configuration.configuration()
    fname = PATH('../config/' + 'configuration.ini')
    CONFIG.fileConfig(fname)

    DEVICENAME = dname
    DEVICE = device.Device(DEVICENAME)

    # initial test environment
    init_env()

    # run test case
    logname = desktop.get_log_name(dname,'TestStartupRegister')
    LogPath = os.path.dirname(os.path.abspath(logname))
    utest_log = os.path.join(LogPath,'unittest.html')

    RESULT_DICT = {}
    FAIL_CASE = []
    try:
        for LOOP_NUM in range(loop):
            fileobj = file(utest_log,'a+')
            suite = unittest.TestLoader().loadTestsFromTestCase(TestStartupRegister)
            #unittest.TextTestRunner(stream=fileobj,verbosity=2).run(suite)
            runner = HTMLTestRunner.HTMLTestRunner(stream=fileobj,verbosity=2,title='Register_Login Testing Report', description = 'Test Result',)
            runner.run(suite)
            fileobj.close()
            sleep(5)
            if LOOP_NUM == loop - 1:
                desktop.summary_result(utest_log, True, RESULT_DICT)
            else:
                desktop.summary_result(utest_log, False, RESULT_DICT)
    except Exception,ex:
        print ex
    fileobj.close()


if __name__ == '__main__':

    run("ZX1G22TG4F", 2)



