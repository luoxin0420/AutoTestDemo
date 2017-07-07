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

        for title in self.omit_cases.split(':'):
            if self._testMethodName.find(title) != -1:
                self.skipTest('this case is not supported by this version')

        logger.info(self._testMethodName + ':Start')

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

                if ok:
                    logger.info(self._testMethodName + ':PASS')
                else:
                    logger.info(self._testMethodName + ':FAILED')
        except Exception,ex:
                print ex

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

        name =''.join([self._testMethodName,'_',str(self.log_count)])
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
            for name in (self.slave_main_process, self.master_service):
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
        #pid = ['17142','1062']
        contens = []
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
                            logger.debug('Find log:' + line)
                            break
                        else:
                            logger.debug('Find log:' + line)
                            if values[2] not in contens:
                                contens.append(values[2])
                except Exception, ex:
                    print ex
                    continue

        # 验证双进程日志
        print len(contens)
        if len(contens) == 2:
            result = True
        else:
            logger.error('Double process log are not complete')

        if not result:
            logger.error('Not found special log information')

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


    #杂志锁屏打开，网络无→W
    def test_network_none_to_wifi(self):

        self.double_process = True
        self.start_app()
        DEVICE.send_keyevent(3)
        # close all network
        DEVICE.wifi_operation('OFF')
        sleep(3)
        DEVICE.gprs_operation('OFF')
        sleep(3)
        if self.double_process:
            self.dump_log_start(self.master_service,'')
        else:
            self.dump_log_start(self.slave_main_process, '')
        # 更新时间到一天后
        DEVICE.update_android_time(1,interval_unit='day')
        DEVICE.gprs_operation('ON')
        sleep(3)
        DEVICE.wifi_operation('ON')
        sleep(60)
        self.dump_log_stop()

        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)

    def test_value(self):

         self.assertEqual(2,2)



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
    #     logger.error(ex)
    #     logger.debug("initial environment is failed")
    #     sys.exit(0)


def run(dname):

    global DEVICENAME, logger, CONFIG, DEVICE,LogPath
    CONFIG = configuration.configuration()
    fname = PATH('../config/' + 'configuration.ini')
    CONFIG.fileConfig(fname)

    DEVICENAME = dname
    DEVICE = device.Device(DEVICENAME)

    # initial test environment
    logname = desktop.get_log_name(dname,'TestTasks')
    LogPath = os.path.dirname(os.path.abspath(logname))
    #logger = desktop.create_logger(logname)
    logger = desktop.Logger(logname)
    init_env()


    # run test case
    utest_log = os.path.join(os.path.dirname(os.path.abspath(logname)),'unit.txt')
    fileobj = file(utest_log,'a+')
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTask)
    unittest.TextTestRunner(stream=fileobj,verbosity=2).run(suite)
    fileobj.close()


if __name__ == '__main__':

    run("ZX1G22TG4F")



