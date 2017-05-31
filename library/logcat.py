#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Xuxh'

import subprocess
import threading
import re
import time
import pJson
from library import desktop


class DumpLogcatFileReader(threading.Thread):

    def __init__(self, mainlog, uid, pkg, filter='', pid_index=0):

        threading.Thread.__init__(self)
        self._mainlog = mainlog
        self._uid = uid
        self._pkg = pkg
        self._pindex = pid_index
        self._filter = filter

    def clear_logcat(self):

        cmd = 'adb -s {0} logcat -c'.format(self._uid)
        subprocess.call(cmd, shell=True)

    def __get_unique_PID(self):

        pid = self.get_PID(self._uid,self._pkg)
        if len(pid) > 0 and int(self._pindex) < len(pid):
            return pid[self._pindex]
        else:
            return 0

    def run(self):
        cmd = self.get_filter_command()
        with open(self._mainlog, 'w+') as outfile:
            self._process = subprocess.Popen(cmd, shell=True, stdout=outfile)

    @staticmethod
    def get_PID(uid,packagename):

        pid = []
        cmd = "adb -s {0} shell ps | grep {1} ".format(uid,packagename)
        sys_name = desktop.get_desktop_os_type()
        if sys_name == 'Windows':
            cmd = cmd + '| awk "{print $2}"'
        else:
            cmd = cmd + "| awk '{print $2}'"
        try:

            popen = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE)
            popen.wait()
            pid = popen.stdout.readlines()

        except KeyboardInterrupt:
            return pid

        return pid

    def get_filter_command(self):

        pid = self.__get_unique_PID()
        for char in ['\r','\n']:
            pid = pid.replace(char,'')
        cmd = ''
        fcmd = ''
        if pid != '':

            basic_cmd = 'adb -s {0} shell logcat -b main -v threadtime '.format(self._uid)
            pcmd = ''.join([' | ', 'grep ', '"', pid, '"'])

            if self._filter != '':
                filter_condition = self._filter.split(';')
                for cond in filter_condition:
                    fcmd = fcmd + ''.join([' | ', 'grep ','"', cond,'"'])

            #cmd = ''.join([basic_cmd, pcmd, fcmd, limit_num, '| awk "{print $7}"'])
            cmd = ''.join([basic_cmd, pcmd, fcmd])

        return cmd

    def stop(self):
        try:
            self._process.terminate()
            print 'wait for logcat stopped...'
            time.sleep(1)
        except Exception, ex:
            print ex


class ParseLogcat(object):

    def __init__(self, fname):

        self._fname = fname

    def get_complete_jsondata(self,keyword):

        Flag = False
        json_data = ''
        prev_data = ''

        with open(self._fname,'r') as rfile:
            for line in rfile:
                # remove redundant space, then divide into group
                line = ' '.join(line.split())
                ll = line.split(' ')
                # get text of logcat
                text = ll[6:]
                str_text = ''.join(list(text))

                if Flag:
                    next_id = str_text[1:8]
                    if next_id == info_id:
                        findstr = '.*(\*{10,}\(\d+\)\*{10,}).*'
                        content = re.compile(findstr)
                        match = content.match(str_text)
                        if match:
                            value = match.group(1)
                        json_data = json_data + str_text.split(value)[1]
                        prev_data = json_data
                    else:
                        Flag = False

                if str_text.lower().find(keyword.lower()) > 0:

                    if json_data != '':
                        prev_data = json_data
                        json_data = ''
                    json_data = json_data + str_text.split(keyword)[1]
                    if str_text.find('**(1)**') > 0:
                        Flag = True
                        info_id = str_text[1:8]
                    else:
                        prev_data = json_data

        return prev_data

    def getUserID(self):

        userID = ''
        keyword =r'.*<uid>(.*)</uid>.*'
        content = re.compile(keyword)
        try:
            with open(self._fname) as file:
                for line in file:
                    m = content.match(line)
                    if m:
                        userID = m.group(1)
                        break
        except Exception,ex:
            print ex
        return userID

    def keywordFilter(self,keyword):

        count = 0

        # Filter file and output to another file
        try:
            filteredFilename = self._fname.split('.')[0] + '_filter.log'
        except Exception,ex:
            print ex

        with open(self._fname, 'r') as rfile, open(filteredFilename, 'w+') as wfile:

            for line in rfile:
                if line.lower().find(keyword.lower()) >= 0:
                    wfile.write(line)
                    count += 1

        if count > 0:
            return True, filteredFilename
        else:
            return False,filteredFilename


def main():

    fname = r'E:\AutoTestDemo\TestAdvertisement\log\20170523\860BCMK22LD8\201705231531\out.log'
    # log = DumpLogcatFileReader(fname, '860BCMK22LD8','com.vlife.mxlock.wallpaper:main','4697956883387773100;query_window_condition_list')
    # log.start()
    # time.sleep(20)
    # log.stop()

    plog = ParseLogcat(fname)
    window_data = plog.get_complete_jsondata('responseDataJson:')
    print window_data
    temp = pJson.parseJson(window_data)
    # value = temp.extract_element_value('l[0].b.z.ok_left_v_background')
    # print value[0]
    # name = value[0][0].split('/')[-1][:-4]
    # url = 'http://stage.3gmimo.com/handpet/' + value[0]
    # print url
    # url = 'http://stage.3gmimo.com/handpet/' + 'f/z/214/19c69e51a58a92bc8cf4215cd470b66f.zip.pet'
    #
    # desktop.download_data(url, r'd:\download.zip')
    #
    # desktop.unzip_file(r'd:\download.zip',r'd:\\')

if __name__ == '__main__':
    main()
