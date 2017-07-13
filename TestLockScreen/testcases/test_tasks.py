#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Xuxh'

import os
try:
    import unittest2 as unittest
except(ImportError):
    import unittest
from time import sleep
from library import configuration
from library import logcat as dumplog
from library import device
from library import desktop
from library import uiautomator
from library import HTMLTestRunner

PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)


class TestTask(unittest.TestCase):

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
        self.log_count = 1
        self.double_process = False
        self.proc_name = 'lockscreen'

        for title in self.omit_cases.split(':'):
            if self._testMethodName.find(title) != -1:
                self.skipTest('this case is not supported by this version')

        if LOOP_NUM != 0:
            self.set_init_env()

        #logger.info(self._testMethodName + ':Start')

        # only connect wifi
        DEVICE.gprs_operation('OFF')
        sleep(5)
        DEVICE.wifi_operation('ON')
        sleep(5)

    def tearDown(self):

        #self._outcomeForDoCleanups = result   # Python 3.2, 3.3
        try:
                if hasattr(self, '_outcome'):  # Python 3.4+
                    result = self.defaultTestResult()  # these 2 methods have no side effects
                    self._feedErrorsToResult(result, self._outcome.errors)
                else:  # Python 3.2 - 3.3 or 2.7
                    result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
                error = self.list2reason(result.errors)
                failure = self.list2reason(result.failures)
                ok = not error and not failure

                #Save all test result
                #init result dict at the first time
                if LOOP_NUM == 0:
                    RESULT_DICT.setdefault(self._testMethodName, {})['Result'] = []
                    RESULT_DICT.setdefault(self._testMethodName, {})['Log'] = []

                if ok:
                    #logger.info(self._testMethodName + ':PASS')
                    RESULT_DICT[self._testMethodName]['Result'].append('PASS')
                    RESULT_DICT[self._testMethodName]['Log'].append('')
                else:
                    #logger.info(self._testMethodName + ':FAILED')
                    RESULT_DICT[self._testMethodName]['Result'].append('FAILED')
                    RESULT_DICT[self._testMethodName]['Log'].append(os.path.basename(self.log_name))
                    # insert into fail case list
                    FAIL_CASE.append(self._testMethodName)

        except Exception,ex:
                print ex

        # only connect wifi
        DEVICE.gprs_operation('OFF')
        sleep(5)
        DEVICE.wifi_operation('ON')
        sleep(5)

        # close all adb to avoid 5037 port occupation
        desktop.close_all_program('adb')
        # restart adb server
        sleep(1)
        DEVICE.restart_adb_server()
        sleep(5)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    def set_init_env(self):

        switcher = {
            'test_1': 'ON:ON',
            'test_2': 'ON:OFF',
            'test_3': 'OFF:ON',
            'test_4': 'OFF:OFF'
        }

        value = self._testMethodName[0:6]
        action = switcher.get(value,'ON:ON').split(':')
        self.set_magazine_app_switch(action[0])
        self.set_security_magazine_switch(action[1])

    def dump_log_start(self, service,filter_condition):

        name =''.join([self._testMethodName,'_',str(LOOP_NUM),'_',str(self.log_count)])
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
            if self.double_process:
                plist = [self.slave_main_process, self.master_service]
            elif self.proc_name == 'lockscreen':
                plist = [self.master_service]
            else:
                plist = [self.slave_main_process]

            for name in plist:
                pid = dumplog.DumpLogcatFileReader.get_PID(DEVICENAME,name)
                if str(pid) > 0:
                    pid[0] = pid[0].strip()
                    pid_list.append(pid[0])
        except Exception,ex:
            print ex
            return []

        return pid_list

    def filter_log_result(self, findstr='GetPushMessageTask starting'):

        result = False
        pid = self.get_pid()
        contens = []
        if self.double_process:
            print 'This is a case of double process, expected log lines are 2'
        with open(self.log_name) as reader:
            for line in reader:
                # remove redundance space
                line = ' '.join(filter(lambda x: x, line.split(' ')))
                values = line.split(' ')
                # values[6:] is text column
                try:
                    text = ' '.join(values[6:])
                    if values[2] in pid and text.find(findstr) != -1:
                        if not self.double_process:
                            result = True
                            print 'Find log:' + line
                            break
                        else:
                            print 'Find log:' + line
                            if values[2] not in contens:
                                contens.append(values[2])
                except Exception, ex:
                    print ex
                    continue

        # 验证双进程日志
        if len(contens) == 2 and self.double_process:
            result = True

        return result

    def start_app(self):

        DEVICE.app_operation('START', service=self.slave_service)
        sleep(5)

    def close_app(self):

        DEVICE.app_operation('CLOSE', service=self.slave_service)
        sleep(5)

    def clear_app(self):

        DEVICE.app_operation('CLEAR', service=self.slave_service)
        DEVICE.app_operation('CLEAR', service='com.android.systemui')
        sleep(5)

    def set_magazine_app_switch(self,action):

        DEVICE.app_operation('START', service=self.slave_service)
        sleep(1)
        findstr = [u'开启',u'安装',u'允许',u'确定']
        DEVICE.do_popup_windows(6,findstr)

        # click setting button
        setting_path = CONFIG.getValue(DEVICENAME,'magazine_wifi_switch').split('|')
        temp =  setting_path[0].split('::')
        location = temp[0]
        index = int(temp[1])

        # click setting button
        uiautomator.click_element_by_id(DEVICENAME,location,index)
        sleep(1)

        # get current state of switch
        temp =  setting_path[1].split('::')
        location = temp[0]
        index = int(temp[1])
        state = uiautomator.get_element_attribute(DEVICENAME,location,index,'checked')

        if action.upper() == 'ON' and state != 'true':
            uiautomator.click_element_by_id(DEVICENAME,location,index)

        if action.upper() == 'OFF' and state == 'true':
            uiautomator.click_element_by_id(DEVICENAME,location,index)

        DEVICE.do_popup_windows(2,[u'关闭'])
        sleep(1)
        #return back to HOME
        DEVICE.send_keyevent(4)
        sleep(3)
        DEVICE.send_keyevent(3)
        sleep(3)

    def set_security_magazine_switch(self,action):

        # open set security UI
        value = CONFIG.getValue(DEVICENAME,'security_setting')
        DEVICE.app_operation('LAUNCH', service=value)
        sleep(1)

         # click setting button
        setting_path = CONFIG.getValue(DEVICENAME,'security_magazine_switch').split('::')
        location = setting_path[0]
        index = int(setting_path[1])

        # check current state
        state = uiautomator.get_element_attribute(DEVICENAME,location,index,'checked')

        if action.upper() == 'ON' and state != 'true':
            uiautomator.click_element_by_id(DEVICENAME,location,index)

        if action.upper() == 'OFF' and state == 'true':
            uiautomator.click_element_by_id(DEVICENAME,location,index)

        #return back to HOME
        DEVICE.send_keyevent(3)

    ##### 以下测试用例 杂志开关,仅WIFI都是开#####
    ###杂志锁屏打开，网络无→W
    # def test_100_env(self):
    #
    #     self.set_magazine_app_switch('ON')
    #     self.set_security_magazine_switch('ON')
    #     self.assertEqual(1,1)

    def test_101_double_proc_gprs_to_wifi(self):

        print 'STEPS: WIFI_OFF>GPRS_ON>UPDATE_TIME>GPRS_OFF>WIFI_ON'
        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)

        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('ON')
        sleep(3)

        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        DEVICE.gprs_operation('OFF')
        sleep(15)
        DEVICE.wifi_operation('ON')
        sleep(60)
        self.dump_log_stop()

        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)

    def test_107_double_proc_none_to_wifi(self):

        print 'STEPS: WIFI_OFF>GPRS_OFF>UPDATE_TIME>WIFI_ON'
        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('OFF')
        sleep(3)

        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        DEVICE.wifi_operation('ON')
        sleep(60)
        self.dump_log_stop()

        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)

    def test_102_lockscreen_WIFIOPEN_SCREEN_OFF_ON(self):
    
        print 'STEPS: WIFI_OPEN>UPDATE_DAY_AFTER_1>SCREEN_OFF_ON'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('ON')
        sleep(3)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        DEVICE.screen_on_off('OFF')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(1)
        # unlock screen
        DEVICE.emulate_swipe_action()
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_103_lockscreen_GPRSOPEN_SCREEN_OFF_ON(self):
    
        print 'STEPS: WIFI_CLOSE>GPRS_ON>UPDATE_DAY_AFTER_1>SCREEN_OFF_ON'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('ON')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        #亮灭屏
        DEVICE.screen_on_off('OFF')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(1)
        DEVICE.emulate_swipe_action()
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,False)
    
    def test_104_lockscreen_WIFIOPEN_SCREEN_OFF_ON2(self):
    
        print 'STEPS: WIFI_ON>UPDATE_HOUR_AFTER_2>SCREEN_OFF_ON'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('ON')
        sleep(5)
        # 更新时间到两小时后
        DEVICE.update_android_time(2)
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        DEVICE.screen_on_off('OFF')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(1)
        DEVICE.emulate_swipe_action()
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,False)
    
    def test_105_main_none_to_wifi(self):
    
        print 'STEPS: WIFI_OFF>GPRS_OFF>UPDATE_TIME>GPRS_OFF>WIFI_ON'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('OFF')
        sleep(3)
        DEVICE.wifi_operation('OFF')
        sleep(3)
        # 更新时间到两小时后
        DEVICE.update_android_time(2)
        sleep(1)
        self.dump_log_start(self.slave_main_process, '')
        sleep(1)
        DEVICE.wifi_operation('ON')
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,False)
    
    def test_106_main_gprs_to_wifi(self):
    
        print 'STEPS: WIFI_OFF>GPRS_OFF>UPDATE_TIME>GPRS_OFF>WIFI_ON'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(5)
        DEVICE.gprs_operation('ON')
        sleep(5)
        # 更新时间到两小时后
        DEVICE.update_android_time(2)
        sleep(1)
        self.dump_log_start(self.slave_main_process, '')
        sleep(1)
        DEVICE.gprs_operation('OFF')
        sleep(15)
        DEVICE.wifi_operation('ON')
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,False)
    
    
    ###### 以下测试用例 杂志开关是开,仅WIFI是关#####
    
    def test_200_env(self):
    
        self.set_magazine_app_switch('OFF')
        self.set_security_magazine_switch('ON')
        self.assertEqual(1,1)
    
    def test_201_double_proc_none_to_gprs(self):
    
        print 'STEPS: WIFI_OFF>GPRS_OFF>UPDATE_TIME>GPRS_ON>WIFI_ON'
        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('OFF')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_202_lockscreen_wifi_to_gprs(self):
    
        print 'STEPS: WIFI_OFF>GPRS_ON>UPDATE_TIME>WIFI_OFF>GPRS_ON'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('OFF')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        DEVICE.wifi_operation('OFF')
        sleep(15)
        DEVICE.gprs_operation('ON')
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_203_main_wifi_to_gprs(self):
    
        print 'STEPS: GPRS_CLOSE>WIFI_ON>WIFI_OFF>GPRS_ON>SCREEN_ON'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('OFF')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
    
        self.dump_log_start(self.slave_main_process, '')
        sleep(1)
        DEVICE.wifi_operation('OFF')
        sleep(15)
        DEVICE.gprs_operation('ON')
        sleep(3)
        #亮屏
        DEVICE.screen_on_off('ON')
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_204_lockscreen_WIFIOPEN(self):
    
        print 'STEPS: WIFI_CLOSE>WIFI_ON>SCREEN_OFF_ON'
        self.start_app()
        DEVICE.send_keyevent(3)
        DEVICE.wifi_operation('ON')
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        DEVICE.screen_on_off('OFF')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(1)
        DEVICE.emulate_swipe_action()
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_205_lockscreen_GPRSOPEN(self):
    
        print 'STEPS: WIFI_CLOSE>GPRS_ON>SCREEN_OFF_ON'
        DEVICE.wifi_operation('OFF')
        sleep(3)
        self.start_app()
        DEVICE.send_keyevent(3)
        DEVICE.gprs_operation('ON')
        sleep(3)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        sleep(1)
        DEVICE.screen_on_off('OFF')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(1)
        DEVICE.emulate_swipe_action()
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_206_main_none_to_wifi2(self):
    
        print 'STEPS: WIFI_CLOSE>GPRS_OFF>UPDATE_TIME>WIFI_ON'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('OFF')
        sleep(5)
        DEVICE.wifi_operation('OFF')
        sleep(5)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.slave_main_process, '')
        sleep(1)
        DEVICE.wifi_operation('ON')
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_207_main_gprs_to_wifi(self):
    
        print 'STEPS: WIFI_OFF>GPRS_ON>UPDATE_TIME>GPRS_OFF>WIFI_ON'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(5)
        DEVICE.gprs_operation('ON')
        sleep(3)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.slave_main_process, '')
        sleep(1)
        DEVICE.gprs_operation('OFF')
        sleep(15)
        DEVICE.wifi_operation('ON')
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    #以下测试用例 杂志开关是关,仅WIFI选项是开#####
    
    def test_300_env(self):
    
        self.set_magazine_app_switch('ON')
        self.set_security_magazine_switch('OFF')
        self.assertEqual(1,1)
    
    def test_301_double_proc_gprs_to_wifi(self):
    
        print 'STEPS: WIFI_OFF>GPRS_ON>UPDATE_TIME>GPRS_OFF>WIFI_ON'
        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)
    
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('ON')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        DEVICE.gprs_operation('OFF')
        sleep(15)
        DEVICE.wifi_operation('ON')
        sleep(60)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_302_double_proc_none_to_wifi(self):
    
        print 'STEPS: WIFI_OFF>GPRS_OFF>UPDATE_TIME>WIFI_ON'
        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)
    
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('OFF')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        DEVICE.wifi_operation('ON')
        sleep(60)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    ###以下测试用例 杂志开关是关,仅WIFI选项是关#####
    
    def test_400_env(self):
    
        self.set_magazine_app_switch('OFF')
        self.set_security_magazine_switch('OFF')
        self.assertEqual(1,1)
    
    def test_401_double_proc_none_to_wifi(self):
    
        print 'STEPS: WIFI_OFF>GPRS_OFF>UPDATE_TIME>WIFI_ON'
        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('OFF')
        sleep(3)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(60)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_402_double_proc_none_to_gprs(self):
    
        print 'STEPS: WIFI_OFF>GPRS_OFF>UPDATE_TIME>GPRS_ON>SCREEN_ON'
        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('OFF')
        sleep(3)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(60)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_403_double_proc_gprs_to_wifi(self):
    
        print 'STEPS: WIFI_OFF>GPRS_ON>UPDATE_TIME>GPRS_OFF>WIFI_ON'
        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('ON')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        DEVICE.gprs_operation('OFF')
        sleep(15)
        DEVICE.wifi_operation('ON')
        sleep(60)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_404_lockscreen_wifi_to_gprs(self):
    
        print 'STEPS: GPRS_OFF>WIFI_ON>UPDATE_TIME>WIFI_OFF>GPRS_ON'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('OFF')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        DEVICE.wifi_operation('OFF')
        sleep(15)
        DEVICE.gprs_operation('ON')
        sleep(30)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_405_lockscreen_wifigprs_to_gprs(self):
    
        print 'STEPS: GPRS_ON>WIFI_ON>UPDATE_TIME>WIFI_OFF'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(3)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.master_service,'')
        DEVICE.wifi_operation('OFF')
        sleep(60)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_406_main_none_to_gprs(self):
    
        print 'STEPS: GPRS_OFF>WIFI_OFF>UPDATE_TIME>GPRS_ON>WAITFOR_5MINS'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('OFF')
        sleep(3)
        DEVICE.wifi_operation('OFF')
        sleep(3)
        # 更新时间到5小时55分钟
        DEVICE.update_android_time(5)
        sleep(2)
        DEVICE.update_android_time(55,interval_unit='minutes')
        sleep(1)
        self.dump_log_start(self.slave_main_process, '')
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.screen_on_off('OFF')
        # 静置五分钟
        sleep(5*60)
        self.dump_log_stop()
    
        # 恢复初始状态
        DEVICE.screen_on_off('ON')
        sleep(1)
        DEVICE.emulate_swipe_action()
        self.result = self.filter_log_result()
        self.assertEqual(self.result,False)
    
    def test_407_main_wifigprs_to_wifi(self):
    
        print 'STEPS: GPRS_ON>WIFI_ON>UPDATE_TIME>GPRS_OFF>'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(3)
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.slave_main_process,'')
        sleep(1)
        DEVICE.gprs_operation('OFF')
        sleep(40)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,False)
    
    def test_408_main_wifi_to_gprs(self):
    
        print 'STEPS: GPRS_OFF>WIFI_ON>UPDATE_TIME>WIFI_OFF>GPRS_ON>SCREEN_ON'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('OFF')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(3)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.slave_main_process,'')
        sleep(1)
        DEVICE.wifi_operation('OFF')
        sleep(15)
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(40)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)
    
    def test_409_main_wifigprs_to_gprs(self):
    
        print 'STEPS: GPRS_ON>WIFI_ON>UPDATE_TIME>WIFI_OFF>SCREEN_ON'
        self.proc_name = 'main'
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(3)
    
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        sleep(1)
        self.dump_log_start(self.slave_main_process,'')
        sleep(1)
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.screen_on_off('ON')
        sleep(60)
        self.dump_log_stop()
    
        self.result = self.filter_log_result()
        self.assertEqual(self.result,False)


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
    #     print "initial environment is failed"
    #     sys.exit(0)


def summary_result(logname):


    #RESULT_DICT = {'TEST1':{'Result':['pass','fail'],'Log': ['test1','test2']},'TEST2':{'Result':['pass','fail'],'Log':['test1','test2']}}
    summary_table = '''
    <table class="table_whole" border="1">
<tr align="right">
<th>TestCase_Name</th>
<th>Test_Result</th>
<th>Log</th>
</tr>
<tr align="right">
${content}
</tr>
</table>
'''
    lines = ''
    for key, value in RESULT_DICT.items():

        result = '<Br/>'.join(value['Result'])
        log = '<Br/>'.join(value['Log'])
        single = ''.join(['<tr><td>',key,'</td>','<td>',result,'</td>','<td>',log,'</td><tr>'])
        # print key)
        # print result)
        # print log)
        lines = lines + single

    summary_table = summary_table.replace('${content}',lines)
    #print summary_table
    count = desktop.get_file_rows(logname)
    report = os.path.join(os.path.dirname(logname),'summary_report2.html')
    i = 1
    with open(report, 'wb') as wfile, open(logname) as rfile:
        for line in rfile:
            if line.find('</body>') == -1:
                wfile.write(line)
            else:
                if count - i == 1:
                    summary_table += '</body>'
                    wfile.write(summary_table)
                else:
                    wfile.write(line)
            i +=1


def run(dname,loop=1):

    global DEVICENAME,CONFIG, DEVICE, LogPath
    global LOOP_NUM, RESULT_DICT, FAIL_CASE

    CONFIG = configuration.configuration()
    fname = PATH('../config/' + 'configuration.ini')
    CONFIG.fileConfig(fname)

    DEVICENAME = dname
    DEVICE = device.Device(DEVICENAME)

    # initial test environment
    init_env()


    # run test case
    logname = desktop.get_log_name(dname,'TestTasks')
    LogPath = os.path.dirname(os.path.abspath(logname))
    utest_log = os.path.join(LogPath,'unittest.html')
    fileobj2 = file(utest_log,'a+')

    ####RESULT_DICT format {casename:{Result:['PASS','PASS'],Log:['','']}}#####
    RESULT_DICT = {}
    FAIL_CASE = []
    for LOOP_NUM in range(loop):

        if LOOP_NUM == 0:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestTask)
        else:
            suite = unittest.TestSuite()
            for name in FAIL_CASE:
                suite.addTest(TestTask(name))
        FAIL_CASE = []
        #unittest.TextTestRunner(stream=fileobj,verbosity=2).run(suite)
        #runner = HtmlTestRunner.HTMLTestRunner(output=DEVICENAME,template=PATH('../ext/' + 'report_template.html'))
        runner =HTMLTestRunner.HTMLTestRunner(stream=fileobj2,verbosity=2,title='Task Testing Report',description='Test Result',)
        runner.run(suite)
    fileobj2.close()
    sleep(5)
    summary_result(RESULT_DICT,utest_log)

if __name__ == '__main__':

    run("ZX1G22TG4F",2)



