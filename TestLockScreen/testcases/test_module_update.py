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
from library import HTMLTestRunner
from library.db import dbmysql
from business import config_srv

PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)


class TestModule(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        self.slave_service = CONFIG.getValue(DEVICENAME,'slave_service')
        self.slave_main_process = self.slave_service + ':main'
        self.omit_cases = CONFIG.getValue(DEVICENAME, 'omit_cases')

    def setUp(self):

        self.log_name = None
        self.log_path = None
        self.log_reader = None
        self.result = False
        self.log_count = 1

        for title in self.omit_cases.split(':'):
            if self._testMethodName.find(title) != -1:
                LOGGER.debug(self._testMethodName + 'SKIP')
                self.skipTest('this case is not supported by this version')
            else:
                LOGGER.debug(self._testMethodName + 'START')

        # only connect wifi
        DEVICE.gprs_operation('OFF')
        sleep(5)
        DEVICE.wifi_operation('ON')
        sleep(5)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

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

            if LOOP_NUM == 0:
                RESULT_DICT.setdefault(self._testMethodName, {})['Result'] = []
                RESULT_DICT.setdefault(self._testMethodName, {})['Log'] = []

            if ok:
                RESULT_DICT[self._testMethodName]['Result'].append('PASS')
                RESULT_DICT[self._testMethodName]['Log'].append('')
                LOGGER.debug(self._testMethodName + ':PASS')
            else:
                RESULT_DICT[self._testMethodName]['Result'].append('FAILED')
                RESULT_DICT[self._testMethodName]['Log'].append(os.path.basename(self.log_name))
                # insert into fail case list
                FAIL_CASE.append(self._testMethodName)
                LOGGER.debug(self._testMethodName + ':FAIL')

        except Exception, ex:
                LOGGER.error(ex)

        # clear
        self.clear_app()
        # close all adb to avoid 5037 port occupation
        desktop.close_all_program('adb')
        # restart adb server
        sleep(1)
        DEVICE.restart_adb_server()
        sleep(5)

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
            pid = dumplog.DumpLogcatFileReader.get_PID(DEVICENAME,self.slave_main_process)
            if str(pid) > 0:
                pid[0] = pid[0].strip()
                pid_list.append(pid[0])
        except Exception,ex:
            print ex
            return []

        return pid_list

    def filter_log_result(self, findstr='databases/system'):

        result = False
        pid = self.get_pid()
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
                        result = True
                        print 'Find log:' + line
                        break
                except Exception, ex:
                    LOGGER.error(ex)
                    continue

        return result

    def clear_app(self):

        DEVICE.app_operation('CLEAR', service=self.slave_service)
        #DEVICE.app_operation('CLEAR', service='com.android.systemui')
        sleep(5)

    def update_db(self,wififlag):

        updateFlag = False
        query = ''
        mid = CONFIG.getValue(DEVICENAME,'background_module_id1')
        query = 'select network from fun_plugin_file where id = {0}'.format(mid)
        result = db.select_one_record(query)
        value = result[0]['network']

        if wififlag and int(value) != 1:
            query = 'update fun_plugin_file set network = 1 where id = {0}'.format(mid)
        if not wififlag and int(value) != 5:
            query = 'update fun_plugin_file set network = 5 where id = {0}'.format(mid)

        if query != '':
            db.execute_update(query)
            updateFlag = True
        return updateFlag

    def enable_module(self):

        config_file = PATH('../../htmlconfig.ini')
        config_srv.enableModule(config_file,'STAGECONFIG')

    def test_100_download_wifi(self):

        print 'STEPS: WIFI_OFF > UPDATE TIME > WIFI_ON'
        DEVICE.send_keyevent(3)

        DEVICE.wifi_operation('OFF')
        sleep(3)

        self.dump_log_start(self.slave_service, '')
        sleep(2)
        DEVICE.update_android_time(1, interval_unit='day')
        sleep(1)
        DEVICE.wifi_operation('ON')
        sleep(60)
        self.dump_log_stop()

        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)

    def test_101_download_enable_GPRS(self):

        print 'STEPS: WIFI_OFF > UPDATE TIME > WIFI_ON'
        DEVICE.send_keyevent(3)

        DEVICE.wifi_operation('OFF')
        sleep(3)

        result = self.update_db(False)
        if result:
            self.enable_module()

        self.dump_log_start(self.slave_service, '')
        sleep(2)
        DEVICE.update_android_time(1, interval_unit='day')
        sleep(1)
        DEVICE.gprs_operation('ON')
        sleep(60)
        self.dump_log_stop()

        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)

    def test_102_download_disable_GPRS(self):

        print 'STEPS: WIFI_OFF > UPDATE TIME > WIFI_ON'

        DEVICE.wifi_operation('OFF')
        sleep(3)

        # make GPRS is disable
        result = self.update_db(True)
        if result:
            self.enable_module()

        self.dump_log_start(self.slave_service, '')
        sleep(2)
        DEVICE.update_android_time(1, interval_unit='day')
        sleep(1)
        DEVICE.gprs_operation('ON')
        sleep(60)
        self.dump_log_stop()

        self.result = self.filter_log_result()
        self.assertEqual(self.result,True)


def init_env():

    db_conf = PATH('../../config/dbconfig.ini')
    db = dbmysql.MysqlDB(db_conf, 'STAGE')
    mid1 = CONFIG.getValue(DEVICENAME,'background_module_id1')
    mid2 = CONFIG.getValue(DEVICENAME,'background_module_id2')
    query = 'select * from fun_plugin_file where id = {0} or id = {1}'.format(mid1,mid2)
    result = db.select_many_record(query)
    if len(result) == 2:
        return result
    else:
        return []


def run(dname, loop, rtype,elog):

    global DEVICENAME,CONFIG, DEVICE, LogPath
    global LOOP_NUM, RESULT_DICT, FAIL_CASE
    global LOGGER, EXPECTED_RESULT,db

    LOGGER = elog
    CONFIG = configuration.configuration()
    fname = PATH('../config/' + 'configuration.ini')
    CONFIG.fileConfig(fname)

    DEVICENAME = dname
    DEVICE = device.Device(DEVICENAME)

    # initial test environment
    result = init_env()

    # get expected result, then run cases
    if len(result) == 2:

        EXPECTED_RESULT = result
        # run test case
        logname = desktop.get_log_name(dname,'TestModules')
        LogPath = os.path.dirname(os.path.abspath(logname))
        utest_log = os.path.join(LogPath,'unittest.html')

        # ##RESULT_DICT format {casename:{Result:['PASS','PASS'],Log:['','']}}#####
        RESULT_DICT = {}
        FAIL_CASE = []

        try:
            for LOOP_NUM in range(loop):

                fileobj = file(utest_log,'a+')
                if LOOP_NUM == 0 or rtype.upper() == 'ALL':
                    suite = unittest.TestLoader().loadTestsFromTestCase(TestModule)
                else:
                    suite = unittest.TestSuite()
                    for name in FAIL_CASE:
                        suite.addTest(TestModule(name))
                    FAIL_CASE = []

                if suite.countTestCases() > 0:
                    runner = HTMLTestRunner.HTMLTestRunner(stream=fileobj, verbosity=2, title='Module Testing Report', description='Test Result',)
                    runner.run(suite)
                fileobj.close()
                sleep(5)
                # write log to summary report
                if LOOP_NUM == loop - 1:
                    desktop.summary_result(utest_log, True, RESULT_DICT)
                else:
                    desktop.summary_result(utest_log, False, RESULT_DICT)

        except Exception, ex:
            print ex

if __name__ == '__main__':

    run("ZX1G22TG4F",2)




