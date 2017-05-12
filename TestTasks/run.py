__author__ = 'Xuxh'

import sys
import argparse
try:
    import unittest2 as unittest
except(ImportError):
    import unittest

from publiclib import library
from publiclib import configuration
from publiclib import myglobal
from types import ModuleType
from testcases import *


def import_module(name):
    """Dynamically imports module and extracts the testcase from
       the end if present.

       This works on zipped packages and python files alike.
       It will not work on pathnames.
    """
    testname = None
    try:
        package = __import__(name)
    except ImportError, e:
        parts = name.rsplit('/', 1)
        if len(parts) != 2:
            return None, None, None
        try:
            package, temp, testname = import_module(parts[0])
        except ImportError:
            raise ImportError('Unable to import %s' % name)
        if testname:
            testname = '.'.join((testname, parts[1]))
        else:
            testname = parts[1]
    return package, package.__name__, testname


def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
        if isinstance(mod,ModuleType):
            module = mod
    return module,mod


if __name__ == '__main__':

    global my_driver
    global my_logger

    newParser = argparse.ArgumentParser()
    newParser.add_argument("-u", "--uid", dest="uid", help="Your device uid")
    newParser.add_argument("-p", "--port", type=int, dest="port", help="Your listen port")
    newParser.add_argument("-b", "--bport", type=int, dest="bport", help="Your bootstrap port")

    args = newParser.parse_args()
    uid = args.uid
    port = args.port
    bport = args.bport

    if uid is None:
        sys.exit(0)
    if port is None:
        sys.exit(0)
    if bport is None:
        sys.exit(0)

    # verify if device is connected
    devices = library.get_connected_devices()
    if uid not in devices:
        print "Device is not connected, please check"
        sys.exit(0)

    try:
        # verify if device is configuration
        config = configuration.configuration()
        config.fileConfig(myglobal.CONFIGURATONINI)
        config.setValue(uid,'port',str(port))
    except Exception, ex:
        print "There is no related configuration information"
        sys.exit(0)

    try:
        pid = 0
        filename = library.get_log_name(uid)
        config.setValue(uid,'logname',filename)
        fileobj = file(filename,'a+')
        status, appium_process = library.launch_appium(uid, port, bport)
        pid = appium_process.pid
        if status == "READY":
            # test_schedule.init_device_environment(uid,port,test_logger,filename)
            # suite = unittest.TestLoader().loadTestsFromTestCase(test_module)
            case_list = config.getValue(uid,'test_list').split(';')
            for cases in case_list:
                module, mod = my_import(cases)
                module.init_device_environment(uid,port,filename)
                suite = unittest.TestLoader().loadTestsFromName(cases)
                unittest.TextTestRunner(stream=fileobj,verbosity=2).run(suite)

    except Exception, ex:
        print ex
    finally:
        if pid != 0:
            # kill responding nodes
            library.kill_child_processes(pid)
            # kill parent process
            appium_process.kill()

