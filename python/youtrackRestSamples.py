# coding=UTF-8

from youtrack.connection import Connection, httplib2
from xml.etree.ElementTree import fromstring
import random
import urllib
import httplib
import urllib2

import socks

httplib2.debuglevel=4
httplib.debuglevel=4

yt = Connection('http://teamsys.intellij.net', 'resttest', 'resttest')#, proxy_info = httplib2.ProxyInfo(socks.PROXY_TYPE_HTTP, 'localhost', 8888))
#yt = Connection('http://localhost:8080', 'root', 'root')

#yt = Connection('http://v-rot-mne-nogi.myjetbrains.com/youtrack', 'root', 'root') #, proxy_info = httplib2.ProxyInfo(socks.PROXY_TYPE_HTTP, 'localhost', 8888))

print 'connected'

# create subsystem
#print yt.createSubsystemDetailed('ADM', 'ss' + str(random.random()), False, 'root')

# get issue
#i = yt.getIssue('SB-4950')

#print i

print yt.createIssue('SB', 'resttest', 'test', 'test', '1', 'Bug', 'Unknown', 'Open', '', '', '')
#print i.getAttachments()
#a = i.getAttachments()[0]
#print a
#
#content = open('socks.py')
#print yt2.createAttachment('ADM-1', a.name, content, 'root', contentLength=int(content.headers.dict['content-length']), contentType=content.info().type)

#i = yt.getIssues('ADM', 'tut', 0, 100)
#print i
#print i[0].getLinks()
#print i[0].getAttachments()
#print i[0].getComments()

#print yt.getSubsystems('JT')
#print yt.getIssue('JT-4832')
#print yt.getProject('JT')
#print yt.getUser('root')
#print yt.createUser('v2', 'v1', 'vadim', 'vadim@vadim.com', 'vadim@vadim.com')
#print yt.importUsers([{'login':'vadim2', 'fullName':'vadim', 'email':'eee@ss.com', 'jabber':'fff@fff.com'},
#                      {'login':'maxim2', 'fullName':'maxim', 'email':'aaa@ss.com', 'jabber':'www@fff.com'}])


#connection.importIssues('ADM', 'group', [
#        {'numberInProject':'1',
#         'summary': 'some summary',
#         'description':'some description',
#         'priority':'1',
#         'fixedVersion':['1.0', '2.0'],
#         'comment':[{'author':'yamaxim', 'text':'comment text', 'created':'1267030230127'},
#                    {'author':'yavadim', 'text':'comment text 2', 'created':'1267030230127'}]
#         },
#        {'numberInProject':'2',
#         'summary':'some problem',
#         'description':'some description',
#         'priority':'1'}])

#print yt.importIssues('JT', 'group', yt.getIssues('JT', '', 100, 3))

#print yt.getIssues('JT', '', 0, 10)


#send: 'GET /rest/issue/SB-4950 HTTP/1.1\r\n
#       Host: teamsys.intellij.net\r\nuser-agent: Python-httplib2/$Rev: 259 $\r\n
#       cookie: JSESSIONID=drgfn16jz02vllov6w3p6gyl;Path=/, jetbrains.charisma.main.security.PRINCIPAL=YzBjZGM3N2UyMmRlYTAyY2I2NzMyZTdlZjc5N2JkYjI5YzdjYWU0NTRmY2I1Zjc5NzBiMmUzY2ZlM2QzZDA2YjpyZXN0dGVzdA;Path=/;Expires=Fri, 17-Jun-2011 10:53:34 GMT\r\\a
#       accept-encoding: compress, gzip\r\ncache-control: no-cache\r\n\r\n'
