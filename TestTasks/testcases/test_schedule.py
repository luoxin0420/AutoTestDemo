# coding=utf-8
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
from TestTasks.publiclib import self_uiautomator


# Returns abs path relative to this file and not cwd
PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)

CONFIG = configuration.configuration()
CONFIG.fileConfig(myglobal.CONFIGURATONINI)

TEMPPATH = r'../temp/'


def init_device_environment(dname,dport,logfname):

    global DEVICENAME, PORT, LOGGER,IMAGEPATH

    DEVICENAME = dname
    PORT = dport
    LOGGER = library.create_logger(logfname)
    IMAGEPATH = os.path.join(os.path.dirname(logfname),'image')
    if not os.path.isdir(IMAGEPATH):
        os.makedirs(IMAGEPATH)

    library.init_app(DEVICENAME)


class TestScheduleTasks(unittest.TestCase):

    # @classmethod
    # def setUpClass(self):
    #
    #     desired_caps = {}
    #     desired_caps['platformName'] = CONFIG.getValue(DEVICENAME,'platformName')
    #     desired_caps['platformVersion'] = CONFIG.getValue(DEVICENAME,'platformVersion')
    #     desired_caps['deviceName'] = DEVICENAME
    #     desired_caps['app'] = PATH('../apps/' + CONFIG.getValue(DEVICENAME,'app'))
    #     #desired_caps['appPackage'] = CONFIG.getValue(DEVICENAME,'appPackage')
    #     #desired_caps['appActivity'] = CONFIG.getValue(DEVICENAME,'appActivity')
    #     self.driver = webdriver.Remote('http://127.0.0.1:' + str(PORT) +'/wd/hub',desired_caps)

    # @classmethod
    # def tearDownClass(self):
    #     self.driver.quit()

    def setUp(self):

        desired_caps = {}
        desired_caps['platformName'] = CONFIG.getValue(DEVICENAME,'platformName')
        desired_caps['platformVersion'] = CONFIG.getValue(DEVICENAME,'platformVersion')
        desired_caps['deviceName'] = DEVICENAME
        #desired_caps['app'] = PATH('../apps/' + CONFIG.getValue(DEVICENAME,'app'))
        desired_caps['appPackage'] = CONFIG.getValue(DEVICENAME,'appPackage')
        desired_caps['appActivity'] = CONFIG.getValue(DEVICENAME,'appActivity')
        self.driver= webdriver.Remote('http://127.0.0.1:' + str(PORT) +'/wd/hub',desired_caps)
        sleep(2)
        
        self.log_name = None
        self.log_path = None
        self.log_object = None
        self.log_reader = None
        LOGGER.debug('Start testing')

    def tearDown(self):

        self.driver.close_app()
        self.driver.quit()
        sleep(2)

    def log_in_application(self):

        # maybe popup window is exist, contain text u'跳过'
        try:
            self.driver.find_element_by_id('com.vlife:id/btn_skip').click()
            sleep(1)
        except Exception,ex:
            print ex

        # if don't log in at first, will directly access to main screen, so try to do twice click
        try:
            #self.driver.start_activity(CONFIG.getValue(DEVICENAME,'appPackage'),'com.vlife/.SplashActivity')
            self.driver.find_element_by_id('com.vlife:id/btn_login').click()
            sleep(3)
        except Exception,ex:
            try:
                self.driver.find_element_by_id('com.vlife:id/guide_go_text').click()
                sleep(3)
            except Exception,ex:
                LOGGER.debug(ex)
        try:
            self.driver.find_element_by_id('com.vlife:id/guide_info').click()
            sleep(3)
        except Exception,ex:
            LOGGER.debug(ex)

        height = self.driver.get_window_size()['height']
        width = self.driver.get_window_size()['width']
        if int(height) > 2000:
            self.driver.swipe(int(width/2),int(height/2+300),int(width/2), int(height/2-500), 1000)
        else:
            self.driver.swipe(int(width/2),int(height/2+200),int(width/2), int(height/2-300), 500)
        sleep(2)
        # For some devices, maybe popup permission window
        for i in range(5):
            try:
                self.driver.find_element_by_id('com.android.packageinstaller:id/permission_allow_button').click()
                sleep(1)
            except Exception,ex:
                print ex
                break
        sleep(5)

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
        #temp = unittest.TestCase.id()
        base_name = '01_log_in' + '.png'
        img_name = os.path.join(IMAGEPATH,base_name)
        self.driver.get_screenshot_as_file(img_name)
        self.dump_log_stop()
        keyword = 'jabber:iq:register'
        result = dumplog.keywordFilter(self.log_path,DEVICENAME,keyword,LOGGER)
        self.assertEqual(True,result)

    def test_02_network_connection_update(self):

        self.log_in_application()
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
        self.driver.close_app()
        sleep(2)
        self.dump_log_start()
        library.wifi_operation(DEVICENAME,'OFF')
        sleep(1)
        library.wifi_operation(DEVICENAME,'ON')
        sleep(3)
        library.update_android_time(DEVICENAME,0)
        sleep(10)
        self.dump_log_stop()
        cur_uid = dumplog.getUserID(self.log_path,DEVICENAME,LOGGER)
        self.assertEqual(orig_uid,cur_uid)

    def test_03_clearcache_uid_update(self):

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
        library.app_operation(DEVICENAME,'LAUNCH')
        sleep(10)
        self.log_in_application()
        sleep(5)
        cur_uid = library.get_userid_from_file(DEVICENAME)
        LOGGER.debug('Get user id from userinfo.xml:'+cur_uid)
        if cur_uid != '':
            self.assertNotEqual(orig_uid,cur_uid)
        else:
            self.assertIsNot(cur_uid,'')


if __name__ == '__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestScheduleTasks)
    unittest.TextTestRunner(verbosity=2).run(suite)


