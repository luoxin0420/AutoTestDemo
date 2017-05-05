__author__ = 'Xuxh'


import os
try:
    import unittest2 as unittest
except(ImportError):
    import unittest
from appium import webdriver
from time import sleep
from datetime import datetime
from appium.webdriver.connectiontype import ConnectionType

from TestTasks.publiclib import configuration
from TestTasks.publiclib import myglobal
from TestTasks.publiclib import library
from TestTasks.publiclib import filterlogcat as dumplog


# Returns abs path relative to this file and not cwd
PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)

CONFIG = configuration.configuration()
CONFIG.fileConfig(myglobal.CONFIGURATONINI)

TEMPPATH = r'../temp/'


def get_device_info(dname,dport,my_logger):
    global DEVICENAME, PORT, LOGGER
    DEVICENAME = dname
    PORT = dport
    LOGGER = my_logger


class TestScheduleTasks(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        desired_caps = {}
        desired_caps['platformName'] = CONFIG.getValue(DEVICENAME,'platformName')
        desired_caps['platformVersion'] = CONFIG.getValue(DEVICENAME,'platformVersion')
        desired_caps['deviceName'] = DEVICENAME
        desired_caps['app'] = PATH('../apps/' + CONFIG.getValue(DEVICENAME,'app'))
        #desired_caps['appPackage'] = CONFIG.getValue(DEVICENAME,'appPackage')
        #desired_caps['appActivity'] = CONFIG.getValue(DEVICENAME,'appActivity')
        self.driver = webdriver.Remote('http://127.0.0.1:' + str(PORT) +'/wd/hub',desired_caps)

    @classmethod
    def tearDownClass(self):
        self.driver.quit()

    def setUp(self):

        self.log_name = None
        self.log_path = None
        self.log_object = None
        self.log_reader = None
        self.app_path = '/data/local/tmp/420log.apk'
        LOGGER.debug('Start testing')

    def tearDown(self):
        self.driver.close_app()

    def init_install_app(self):
        try:
            if not self.driver.is_app_installed(CONFIG.getValue(DEVICENAME,'appPackage')):
                sleep(15)
                LOGGER.debug('Package is not found, then install')
                if not self.driver.is_app_installed(CONFIG.getValue(DEVICENAME,'appPackage')):
                    library.app_operation(DEVICENAME,'INSTALL',self.app_path)
            try:
                self.log_in_application()
            except Exception, ex:
                print ex
        except Exception,ex:
            print ex

    def log_in_application(self):

        try:
            self.driver.start_activity(CONFIG.getValue(DEVICENAME,'appPackage'),CONFIG.getValue(DEVICENAME,'appActivity'))
            sleep(15)
            self.driver.find_element_by_id('com.vlife:id/btn_login').click()
            sleep(3)
            self.driver.find_element_by_id('com.vlife:id/guide_info').click()
            sleep(3)
            height = self.driver.get_window_size()['height']
            width = self.driver.get_window_size()['width']
            self.driver.swipe(int(width/2),int(height/2+200),int(width/2), int(height/2-300), 500)
            sleep(3)
        except Exception,ex:
            LOGGER.debug(ex)

    def dump_log_start(self):

        self.log_name =''.join([DEVICENAME,'_',datetime.now().strftime('%Y%m%d%H%M'), 'log.txt'])
        self.log_path = PATH(TEMPPATH+self.log_name)
        self.log_object = open(self.log_path, 'w+')
        self.log_reader = dumplog.DumpLogcatFileReader(self.log_object,DEVICENAME)
        self.log_reader.start()

    def dump_log_stop(self):

        self.log_reader.stop()
        self.log_object.close()

    def test_01_log_in(self):

        self.dump_log_start()
        self.log_in_application()
        self.dump_log_stop()
        keyword = 'jabber:iq:register'
        result = dumplog.keywordFilter(self.log_path,DEVICENAME,keyword,LOGGER)
        self.assertEqual(True,result)

    def test_02_network_connection_update(self):

        self.init_install_app()
        orig_uid = library.get_userid_from_file(DEVICENAME)
        LOGGER.debug('Get user id from userinfo.xml:'+orig_uid)

        # change network status
        #value = self.driver.network_connection()
        # get network
        # 0=None 1=Airplane 2=wifi 4=data 6=all network on
        #self.driver.network_connection # it would return int type, like 0, 1, 2, 4, 6
        # print ConnectionType(self.driver.network_connection).name
        # self.driver.set_network_connection(ConnectionType.NO_CONNECTION)
        # sleep(2)
        # print ConnectionType(self.driver.network_connection).name
        # self.driver.set_network_connection(ConnectionType.WIFI_ONLY)
        library.app_operation(DEVICENAME,'LAUNCH')
        self.driver.close_app()
        sleep(2)
        self.dump_log_start()
        library.wifi_operation(DEVICENAME,'OFF')
        sleep(1)
        library.wifi_operation(DEVICENAME,'ON')
        sleep(3)
        library.update_android_time(DEVICENAME)
        sleep(5)
        self.dump_log_stop()
        cur_uid = dumplog.getUserID(self.log_path,DEVICENAME,LOGGER)
        self.assertEqual(orig_uid,cur_uid)

    def test_03_clearcache_uid_update(self):

        self.init_install_app()
        sleep(5)
        orig_uid = library.get_userid_from_file(DEVICENAME)
        LOGGER.debug('Get user id from userinfo.xml:'+orig_uid)

        # clear cache and uninstall
        library.app_operation(DEVICENAME,'CLEAR')
        # library.app_operation(DEVICENAME,'UNINSTALL')
        # sleep(2)
        # library.app_operation(DEVICENAME,'INSTALL',self.app_path)
        # sleep(10)

        # install and read file
        self.init_install_app()
        sleep(5)
        cur_uid = library.get_userid_from_file(DEVICENAME)
        LOGGER.debug('Get user id from userinfo.xml:'+cur_uid)
        self.assertNotEqual(orig_uid,cur_uid)

if __name__ == '__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestScheduleTasks)
    unittest.TextTestRunner(verbosity=2).run(suite)


