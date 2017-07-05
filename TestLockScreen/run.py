__author__ = 'Xuxh'

import sys
import argparse
try:
    import unittest2 as unittest
except(ImportError):
    import unittest

from library import device
from library import configuration
from library import myglobal
from testcases import test_startup_register

if __name__ == '__main__':

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

    try:
        # verify if device is configuration
        config = configuration.configuration()
        config.fileConfig(myglobal.CONFIGURATONINI)
    except Exception, ex:
        print "There is no related configuration information"
        sys.exit(0)

    try:
        case_list = config.getValue(uid,'test_list').split(';')
        for cases in case_list:
            if cases.startswith('test_startup_register'):
                test_startup_register.run(uid)

    except Exception, ex:
        print ex



