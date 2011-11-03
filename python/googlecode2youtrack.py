from youtrack.connection import Connection
from urllib import unquote
import youtrack
import gdata.projecthosting.client
import gdata.projecthosting.data
import gdata.gauth
import gdata.client
import gdata.data
import atom.http_core
import atom.core
import datetime, calendar
#from sets import Set
import sys
import urllib
import re
import xml.sax.saxutils
import urllib2

# init mapping
import googleCode
#import
import googleCode.spock
#import googleCode.youtrackAndroid

def main():

#    source_login = 'xxx'
#    source_password = 'xxx'
#
#    target_url = 'http://v-rot-mne-nogi.myjetbrains.com/youtrack'
#    #target_url = 'http://localhost:8080'
#    target_login = 'root'
#    target_password = 'root'
#
#    projectId = 'ADM'
    try:
        len(googleCode.STATES)
        len(googleCode.PRIORITIES)
        len(googleCode.TYPES)
    except BaseException :
        print "You have to import mapping scheme"
        return

    try:
        #source_login, source_password, target_url, target_login, target_password, projectName, projectId = sys.argv[1:]
        source_login = 'anna.zhdan@gmail.com'
        source_password = '94829482'
        target_url = 'http://spockframework.myjetbrains.com/youtrack'
        #target_url = 'http://localhost:8081'
        target_login = 'root'
        target_password = 'jetbrains'
        projectName = 'spock'
        projectId = 'SP'
    except BaseException:
        print "Usage: google2youtrack google_login google_password target_url target_login target_password googleProjectName targetProjectId"
        return

    googlecode2youtrack(source_login, source_password, target_url, target_login, target_password, projectName, projectId)

def findLabel(labels, mapping):
    for l in labels:
        if mapping.has_key(l):
            return mapping[l]

    return None

def type(labels):
    return findLabel(labels, googleCode.TYPES)

def priority(labels):
    return findLabel(labels, googleCode.PRIORITIES)

def getLabels(i):
    return [e.text for e in i.label]

def isCustomField(label):
    for cf in googleCode.CUSTOM_FIELDS:
        if label.startswith(cf):
            return True
    return False

def getTags(labels):
    res = []
    for k in labels:
        if not (googleCode.TYPES.has_key(k) or googleCode.PRIORITIES.has_key(k) or isCustomField(k)):
            res.append(k)
    return res

def issueId(i):
    return i.get_elements(tag='id', namespace='http://schemas.google.com/projecthosting/issues/2009')[0].text

def isResolved(i):
    return i.state.text == 'open'

def getStars(i):
    return i.stars.text

def getDefaultState(i):
    return googleCode.DEFAULT_RESOLVED_STATUS if isResolved(i) else googleCode.DEFAULT_UNRESOLVED_STATUS 

def getState(i):
    if hasattr(i, 'status'):
        s = i.status
        if s is not None:
            status = s.text
            return googleCode.STATES[status] if googleCode.STATES.has_key(status) else getDefaultState(i)

    return getDefaultState(i)

def getReporter(i):
    return i.author[0].name.text

def getAssignee(i):
    if hasattr(i, 'owner') and i.owner is not None:
        return i.owner.username.text

    return None

def toYouTrackComment(c):
    ytc = youtrack.Comment()
    ytc.author = getReporter(c)
    content_text = c.content.text
    if content_text is not None:
        ytc.text = content_text.encode('utf-8')
    else :
        ytc.text = None
    ytc.created = toUnixDate(c.published.text)        
    return ytc if ytc.text is not None else None

def getCustomFieldValues(i):
    res = {}
    for cfname in googleCode.CUSTOM_FIELDS:
        cf = googleCode.CUSTOM_FIELDS[cfname]
        for label in getLabels(i):
            if label.startswith(cfname + "-"):
                if not res.has_key(cf['name']):
                    res[cf['name']] = set([])
                res[cf['name']].add(label[len(cfname)+1:])
    return res

def toYouTrackIssue(i, comments):
    y = youtrack.Issue()
    y.numberInProject = issueId(i)
    y.summary = i.title.text.encode('utf-8')
    y.description = i.content.text.encode('utf-8')
    y.created = toUnixDate(i.published.text)
    y.updated = toUnixDate(i.updated.text)
    y.reporterName = getReporter(i)
    y.assigneeName = getAssignee(i)
    y.state = getState(i)

    labels = getLabels(i)
    y.type = type(labels)
    y.priority = priority(labels)

    # custom fields
    customFieldValues = getCustomFieldValues(i)
    for cf in customFieldValues:
        y[cf] = customFieldValues[cf]

    # comments                
    y.comments = []
    for c in comments:
        ytc = toYouTrackComment(c)
        if ytc is not None:
            y.comments.append(ytc)

    return y

def toYouTrackUser(login):
    u = youtrack.User()
    u.login = login
    u.email = login
    u.jabber = login

    if login.find('@') == -1:
        u.email += "@gmail.com"
        u.jabber += "@gmail.com"

    return u

def toUnixDate(dt_str):
    dt, _, us = dt_str.partition(".")
    dt = datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    us = int(us.rstrip("Z"), 10)
    res = dt + datetime.timedelta(microseconds=us)
    return str(calendar.timegm(res.timetuple()) * 1000)

def getIssueHref(issue):
    return filter(lambda l: l.rel == 'alternate', issue.link)[0].href

def getAttachments(projectName, issue):
    content = urllib.urlopen(getIssueHref(issue)).read()

    attach = re.compile('<a href="(http://' + projectName + '\.googlecode\.com/issues/attachment\?aid=\S+name=(\S+)&\S+)">Download</a>')

    res = []
    for m in attach.finditer(content):
        res.append((xml.sax.saxutils.unescape(m.group(1)), m.group(2)))

    return res        

def getAttachmentContent(url):
    f = urllib2.urlopen(urllib2.Request(url))
    return f

def googlecode2youtrack(source_login, source_password, target_url, target_login, target_password, projectName, projectId):
    source = gdata.projecthosting.client.ProjectHostingClient()
    source.client_login(source_login, source_password, source='youtrack', service='code')
    target = Connection(target_url, target_login, target_password)

    # create project
    print "Create project [" + projectName + "]"    
    try:
        print target.getProject(projectId)
    except youtrack.YouTrackException:
        print target.createProjectDetailed(projectId, projectName, ' ', target_login)

    # create custom fields
    print "Create custom fields"
    for cs in googleCode.CUSTOM_FIELDS:
        ytcs = googleCode.CUSTOM_FIELDS[cs]

        try:
            cfname = ytcs['name']
            print target.createCustomFieldDetailed(cfname, ytcs['type'], ytcs['isPrivate'], ytcs['defaultVisibility'])
        except youtrack.YouTrackException, e:
            print e

        try:
            print target.createEnumBundleDetailed(cfname, [])
        except youtrack.YouTrackException, e:
            print e

        try:
            print target.createProjectCustomFieldDetailed(projectId, cfname, ytcs['empty'], params={'bundle': cfname})
        except youtrack.YouTrackException, e:
            print e


    print "Import issues"
    createdUsers = set([])
    createdCustomFieldValues = {}
    for cf in googleCode.CUSTOM_FIELDS:
        cf_name = googleCode.CUSTOM_FIELDS[cf]['name']
        createdCustomFieldValues[cf_name] = set([])

    start = 1
    max = 30

    while True:
        source = gdata.projecthosting.client.ProjectHostingClient()
        print "Get issues from " + str(start) + " to " + str(start + max)
        query = gdata.projecthosting.client.Query(start_index=start, max_results=max)
        issues = source.get_issues(projectName, query=query).entry
        start += max

        if len(issues) <= 0:
            break

        users = set([])

        ytissues = []
        for issue in issues:
            print "Process issue [" + issueId(issue) + "]"

            # custom fields values
            customFieldValues = getCustomFieldValues(issue)
            for cf in customFieldValues:
                toAdd = customFieldValues[cf].difference(createdCustomFieldValues[cf])
                createdCustomFieldValues[cf] = createdCustomFieldValues[cf].union(customFieldValues[cf])
                if len(toAdd) > 0:
                    print "To enum [" + cf + "] add values " + str(toAdd)
                    try:
                        if cf == 'Subsystem':
                            for v in toAdd :
                                try :
                                    target.createSubsystemDetailed(projectId, v, False, target_login)
                                except youtrack.YouTrackException:
                                    print "Can't create subsystem with name [ %s ]" % v
                        if cf == 'Fix Versions':
                            for v in toAdd :
                                try :
                                    target.createVersionDetailed(projectId, v, False, False)
                                except youtrack.YouTrackException:
                                    print "Can't create version with name [ %s ]" % v
                        target.addValuesToEnumBundle(cf, toAdd)
                    except youtrack.YouTrackException, e:
                        print e                                                            

            ytissue = toYouTrackIssue(issue, source.get_comments(projectName, issueId(issue)).entry)
            ytissues.append(ytissue)

            users.add(toYouTrackUser(ytissue.reporterName))
            if ytissue.hasAssignee():
                users.add(toYouTrackUser(ytissue.assigneeName))

            for comment in ytissue.getComments():
                users.add(toYouTrackUser(comment.author))

        users = users.difference(createdUsers)
        print "Create users [" + str(len(users)) + "]"
        print target.importUsers(users)
        createdUsers = createdUsers.union(users)

        print "Create issues [" + str(len(issues)) + "]"
        print target.importIssues(projectId, projectName + ' Assignees', ytissues)

        print "Add tags to imported issues"
        for issue in issues:
            tags = getTags(getLabels(issue))

            if len(tags) > 0:
                print "For issue [" + issueId(issue) + "] add tags " + str(tags)
                
                for label in tags:
                    try:
                        target.executeCommand(projectId + "-" + issueId(issue), "tag " + label.encode('utf-8'))
                    except youtrack.YouTrackException, e:
                        print e

    print "Transfer attachments"
    start = 1
    max = 100
    while True:
        print "Get issues from " + str(start) + " to " + str(start + max)
        query = gdata.projecthosting.client.Query(start_index=start, max_results=max)
        issues = source.get_issues(projectName, query=query).entry
        start += max

        if len(issues) <= 0:
            break

        for issue in issues:
            print "Process issue [" + issueId(issue) + "]"
            for (url, name) in getAttachments(projectName, issue):
                print "  Transfer attachment [" + name + "]"
                content = urllib2.urlopen(urllib2.Request(url))
                print target.createAttachment(projectId + "-" + issueId(issue), unquote(name).decode('utf-8'), content, target_login,
                                     contentLength=int(content.headers.dict['content-length']),
                                     #contentType=content.info().type, octet/stream always :(
                                     created=None,
                                     group=None)


#            for a in issue.getAttachments():
#                print "Transfer attachment of " + issue.id + ": " + a.name
#                # TODO: add authorLogin to workaround http://youtrack.jetbrains.net/issue/JT-6082
#                a.authorLogin = target_login
#                target.createAttachmentFromAttachment(issue.id, a)



    # create issue links

if __name__ == "__main__":
    main()
