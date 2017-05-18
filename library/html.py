#! /usr/bin/env python
# coding=utf-8
__author__ = 'Xuxh'

import urllib2
import json
import hashlib

from poster.streaminghttp import StreamingHTTPHandler, StreamingHTTPRedirectHandler, StreamingHTTPSHandler
from poster.encode import multipart_encode
import objectpath

import myglobal
import db


class HttpObject(object):

    def __init__(self, url, channalid):

        self.url = url
        self.cid = channalid
        self.apikey = db.get_fieldValue(self.cid, 'apikey')
        self.secret = db.get_fieldValue(self.cid, 'secret')
        self.uid = myglobal.UID
        pass

    def __get_sig_value(self, number):

        '''
        (substr($pwd,0,6).$uid.substr($pwd,6,7).$tel.substr($pwd,13,4).$uid.substr($pwd,17,4).$apikey.substr($pwd,21,6).$tel,$sig,5,32,'sha1')
        '''

        constr = ''
        SECRET = self.secret

        if SECRET == 'NONE':
            constr = ''.join([constr, str(self.uid), str(number), str(self.uid), str(self.apikey), str(number)])
        else:

            constr = ''.join(
                [constr, SECRET[0:6], str(self.uid), SECRET[6:13], str(number), SECRET[13:17], str(self.uid),
                 SECRET[17:21], str(self.apikey) + SECRET[21:27] + str(number)])
        sig = hashlib.sha1(constr).hexdigest()
        sig = sig[5:37]

        return sig

    def get_solr_data(self, number):

        try:
            url = ''.join([self.url, "?tel=", str(number)])
            response = urllib2.urlopen(url)
            if response.getcode() == 200:
                data = response.read()
        except urllib2.HTTPError, ex:
            print ex.code

        return data

    def __get_snapshot_type(key):

        stype = myglobal.SNAPSHOT_TYPE

        if key in stype.keys():
            return stype[key]
        else:
            return 0

    def resolved_number(self, number):

        data = ''
        url = ''

        try:
            sig = self.__get_sig_value(number)
            url = ''.join([self.url, "?apikey=", self.apikey, "&uid=", self.uid, "&tel=", str(number), "&sig=", sig])
            response = urllib2.urlopen(url)
            if response.getcode() == 200:
                data = response.read()
        except urllib2.HTTPError, ex:
            print ex.code

        return data

    def get_test_number(self, limit):

        test_data = []
        try:
            if self.cid != 0:
                # call api to filter data from database
                url = "".join([self.url, "?channelid=", str(self.cid), "&limit=", str(limit)])
                response = urllib2.urlopen(url)
                if response.getcode() == 200:
                    res = response.read()
                    jsondata = json.loads(res)
                    status = jsondata.get('status', '')
                    if status == "success":
                        tree = objectpath.Tree(jsondata)
                        value = tree.execute("$..data.(id,tel,name)")
                        test_data = list(value)
        except Exception, ex:
            print ex
            # test_data = [{'tel': u'10010', 'id': u'5', 'name': u'\u4e2d\u56fd\u8054\u901a'}]
        return test_data

    def upload_images(self, telid, pages):

        try:
            handlers = [StreamingHTTPHandler, StreamingHTTPRedirectHandler, StreamingHTTPSHandler]
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)

            params = {'id': telid}
            i = 0
            while i < len(pages):
                fkey = 'file[index]'.replace('index', str(i))
                params[fkey] = open(pages[i]['name'], 'rb')
                tkey = 'filetype[index]'.replace('index', str(i))
                params[tkey] = pages[i]['type']
                skey = 'file_is_query[index]'.replace('index', str(i))
                if pages[i]['result']:
                    params[skey] = str(1)
                else:
                    params[skey] = str(0)
                i += 1
        # print params
            datagen, headers = multipart_encode(params)
            request = urllib2.Request(self.url, datagen, headers)
            response = urllib2.urlopen(request)
            res = response.read()
            if json.loads(res).get('status', '') == 'success':
                return True
        except Exception, ex:

            print ex

        return False
