__author__ = 'Xuxh'

import subprocess
import threading
import time
from datetime import datetime
import re
from os import path
import os

import library

PATH_BASE = r'temp/'
FILTER_WIH_PID = True


class DumpLogcatFileReader(threading.Thread):

    def __init__(self, mainlog, uid):

        threading.Thread.__init__(self)
        self._mainlog = mainlog
        self._uid = uid

    def run(self):

        cmd = 'adb -s {0} logcat -c'.format(self._uid)
        subprocess.call(cmd, shell=True)
        self._process = subprocess.Popen('adb shell logcat -b main -v threadtime', stdout=self._mainlog)

    def stop(self):
        self._process.terminate()
        print 'wait for logcat stopped...'
        time.sleep(1)


# def shellPIPE(cmd):
#     p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     out, err = p.communicate()
#     return out


def readFile(filename):
    try:
        with open(filename) as file:
            for line in file:
                return line
                break
    except IOError as e:
        print e


def writeFile(filename, str):

    file = open(filename,'w')
    file.write(str)
    file.close()


def keywordFilter(filename, devicename, keyword, logger):

    count = 0
    pid = getProcessId(devicename)
    # Filter file and output to another file
    filteredFilename = filename.split('.')[0] + '_filter.log'
    filteredFile = open(filteredFilename, 'w+')

    with open(filename) as file:

        for line in file:

            ll = line.split(' ')
            if pid != ll[2]:
                continue

            if line.lower().find(keyword.lower()) >= 0:
                filteredFile.write(line)
                count +=1

    filteredFile.close()
    logger.debug('filter file path:' + filteredFilename)

    if count > 0:
        return True
    else:
        return False


def getUserID(filename,devicename,logger):

    userID = ''
    pid = getProcessId(devicename)
    keyword =r'.*<uid>(.*)</uid>.*'
    content = re.compile(keyword)
    try:
        with open(filename) as file:

            for line in file:

                ll = line.split(' ')
                if pid != ll[2]:
                    continue
                m = content.match(line)
                if m:
                    userID = m.group(1)
                    break
    except Exception,ex:
        print ex

    logger.debug('Get current user id:' + userID)

    return userID


def getProcessId(uid):

    cmd = 'adb -s {0} shell dumpsys activity top'.format(uid)
    out = library.shellPIPE(cmd)
    filename = ''.join([uid,datetime.now().strftime('%Y%m%d%H%M%S'),'top.txt'])
    dir = path.join(os.getcwd(),PATH_BASE)
    topProcessFile = path.join(dir, filename)
    myFile = open(topProcessFile, 'w+')
    myFile.write(out)
    myFile.seek(0, 0);

    activity = ""
    pid = ""

    for eachLine in myFile:
      if "pid=" in eachLine:
          activity = eachLine.split(" ")[3].strip()
          pid = eachLine.split("pid=")[-1].strip()
          break
    myFile.close()
    return pid


def main():

    filename = r'E:\MyProjects\TestTasks\temp\HC37VW903116_201704261750log_filter.log'
    pid = '20667'
    keyword = 'jabber:iq:register'
    result = getUserID(filename, pid)
    print result


if __name__ == '__main__':
    main()
