__author__ = 'Xuxh'

import sys
import argparse
import os
try:
    import unittest2 as unittest
except(ImportError):
    import unittest

from publiclib import library
from publiclib import configuration
from publiclib import myglobal
from testcases import test_schedule


def import_file(name):
    """Dynamically loads the given file."""
    dirname, filename = os.path.split(name)
    sys.path.append(dirname)
    try:
        module, modname, testname = import_module(filename)
    finally:
        sys.path.pop(-1)
    return module


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

def load_package(name, testlist):
        """Dynamically loads tests from the given package/module. """
        # Unlike import, __import__ only accepts '/' hierachy notation
        name = name.replace('.', '/')
        try:
            module, name, testname = import_module(name)
        except ImportError, ex:
            print ex

        if testname:
            testlist.append(testname)
        else:
            print name


def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


if __name__ == '__main__':

    global my_driver
    global my_logger

    #module,name,testname = load_package('testcases.test_schedule',[])

    test_module = my_import('testcases.test_schedule.TestScheduleTasks')

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
        DEVICE = config.setValue(uid,'port',str(port))
    except Exception, ex:
        print "There is no related configuration information"
        sys.exit(0)

    try:

        filename,my_logger = library.create_logger(uid)
        fileobj = file(filename,'a+')
        status, appium_process = library.launch_appium(uid, port, bport)
        pid = appium_process.pid
        if status == "READY":
            test_schedule.get_device_info(uid,port,my_logger)
            suite = unittest.TestLoader().loadTestsFromTestCase(test_module)
            unittest.TextTestRunner(stream=fileobj,verbosity=2).run(suite)
    except Exception, ex:
        my_logger.error(ex)
    finally:
        if pid != 0:
            # kill responding nodes
            library.kill_child_processes(pid)
            # kill parent process
            appium_process.kill()

