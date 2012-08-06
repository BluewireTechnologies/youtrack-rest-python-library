import calendar
from datetime import datetime
import httplib2
from xml.dom import minidom
import youtrack
from xml.dom import Node
import urllib2
import urllib
from xml.sax.saxutils import escape, quoteattr
import json
import urllib2_file

class Connection(object):
    def __init__(self, url, login, password, proxy_info=None):
        self.http = httplib2.Http() if proxy_info is None else httplib2.Http(proxy_info=proxy_info)
        self.url = url
        self.baseUrl = url + "/rest"
        self._login(login, password)

    def _login(self, login, password):
        response, content = self.http.request(
            self.baseUrl + "/user/login?login=" + login + "&password=" + password, 'POST',
            headers={'Content-Length': '0'})
        if response.status != 200:
            raise youtrack.YouTrackException('/user/login', response, content)
        self.headers = {'Cookie': response['set-cookie'],
                        'Cache-Control': 'no-cache'}

        #print responsetes


    def _req(self, method, url, body=None, ignoreStatus=None):
        headers = self.headers

        if method == 'PUT' or method == 'POST':
            headers = headers.copy()
            headers['Content-Type'] = 'application/xml; charset=UTF-8'
            headers['Content-Length'] = str(len(body)) if body else '0'

        response, content = self.http.request((self.baseUrl + url).encode('utf-8'), method, headers=headers, body=body)
        if response.status != 200 and response.status != 201 and (ignoreStatus != response.status):
            raise youtrack.YouTrackException(url, response, content)

        #print response

        return response, content

    def _reqXml(self, method, url, body=None, ignoreStatus=None):
        response, content = self._req(method, url, body, ignoreStatus)
        if response.has_key('content-type'):
            if (response["content-type"].find('application/xml') != -1 or response["content-type"].find(
                'text/xml') != -1) and content is not None and content != '':
                try:
                    return minidom.parseString(content)
                except Exception:
                    return ""
            elif response['content-type'].find('application/json') != -1 and content is not None and content != '':
                try:
                    return json.loads(content)
                except Exception:
                    return ""

        if method == 'PUT' and ('location' in response.keys()):
            return 'Created: ' + response['location']
        else:
            return content

    def _get(self, url):
        return self._reqXml('GET', url)

    def _put(self, url):
        return self._reqXml('PUT', url, '<empty/>\n\n')

    def getIssue(self, id):
        return youtrack.Issue(self._get("/issue/" + id), self)

    def createIssue(self, project, assignee, summary, description, priority=None, type=None, subsystem=None, state=None, affectsVersion=None,
                    fixedVersion=None, fixedInBuild=None):
        params = {'project' : project,
                  'summary' : summary,
                  'description' : description}
        if assignee is not None:
            params['assignee'] = assignee
        if priority is not None:
            params['priority'] = priority
        if type is not None:
            params['type'] = type
        if subsystem is not None:
            params['subsystem'] = subsystem
        if state is not None:
            params['state'] = state
        if affectsVersion is not None:
            params['affectsVersion'] = affectsVersion
        if fixedVersion is not None:
            params['fixVersion'] = fixedVersion
        if fixedInBuild is not None:
            params['fixedInBuild'] = fixedInBuild

        return self._reqXml('PUT', '/issue?' + urllib.urlencode(params), '')

    def get_changes_for_issue(self, issue):
        return [youtrack.IssueChange(change, self) for change in self._get("/issue/%s/changes" % issue).getElementsByTagName('change')]

    def getComments(self, id):
        response, content = self._req('GET', '/issue/' + id + '/comment')
        xml = minidom.parseString(content)
        return [youtrack.Comment(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def getAttachments(self, id):
        response, content = self._req('GET', '/issue/' + id + '/attachment')
        xml = minidom.parseString(content)
        return [youtrack.Attachment(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def getAttachmentContent(self, url):
        f = urllib2.urlopen(urllib2.Request(self.url + url, headers=self.headers))
        return f

    def createAttachmentFromAttachment(self, issueId, a):
        content = a.getContent()
        return self.importAttachment(issueId, a.name, content, a.authorLogin,
            contentLength=int(content.headers.dict['content-length']),
            contentType=content.info().type,
            created=a.created if hasattr(a, 'created') else None,
            group=a.group if hasattr(a, 'group') else '')

    def _process_attachmnets(self, authorLogin, content, contentLength, contentType, created, group, issueId, name,
                             url_prefix='/issue/'):
        if contentLength is not None:
            content.contentLength = contentLength
        if contentType is not None:
            content.contentType = contentType

        #post_data = {'attachment': content}
        post_data = {name: content}
        headers = self.headers.copy()
        #headers['Content-Type'] = contentType
        # name without extension to workaround: http://youtrack.jetbrains.net/issue/JT-6110
        params = {#'name': os.path.splitext(name)[0],
                  'authorLogin': authorLogin,
                  }
        if group is not None:
            params["group"] = group
        if created is not None:
            params['created'] = created
        else:
            try:
                params['created'] = self.getIssue(issueId).created
            except youtrack.YouTrackException:
                params['created'] = str(calendar.timegm(datetime.now().timetuple()) * 1000)

        r = urllib2.Request(self.baseUrl + url_prefix + issueId + "/attachment?" +
                            urllib.urlencode(params),
            headers=headers, data=post_data)
        #r.set_proxy('localhost:8888', 'http')
        try:
            res = urllib2.urlopen(r)
        except urllib2.HTTPError, e:
            if e.code == 201:
                return e.msg + ' ' + name
            raise e
        return res

    def createAttachment(self, issueId, name, content, authorLogin='', contentType=None, contentLength=None,
                         created=None, group=''):
        return self._process_attachmnets(authorLogin, content, contentLength, contentType, created, group, issueId,
            name)

    def importAttachment(self, issue_id, name, content, authorLogin, contentType, contentLength, created=None,
                         group=''):
        return self._process_attachmnets(authorLogin, content, contentLength, contentType, created, group, issue_id,
            name, '/import/')


    def getLinks(self, id, outwardOnly=False):
        response, content = self._req('GET', '/issue/' + urllib.quote(id) + '/link')
        xml = minidom.parseString(content)
        res = []
        for c in [e for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]:
            link = youtrack.Link(c, self)
            if link.source == id or not outwardOnly:
                res.append(link)
        return res

    def getUser(self, login):
        """ http://confluence.jetbrains.net/display/YTD2/GET+user
        """
        return youtrack.User(self._get("/admin/user/" + urllib.quote(login.encode('utf8'))), self)

    def createUser(self, user):
        """ user from getUser
        """
        # self.createUserDetailed(user.login, user.fullName, user.email, user.jabber)
        self.importUsers([user])

    def createUserDetailed(self, login, fullName, email, jabber):
        print self.importUsers([{'login': login, 'fullName': fullName, 'email': email, 'jabber': jabber}])

    #        return self._put('/admin/user/' + login + '?' +
    #                         'password=' + password +
    #                         '&fullName=' + fullName +
    #                         '&email=' + email +
    #                         '&jabber=' + jabber)


    def importUsers(self, users):
        """ Import users, returns import result (http://confluence.jetbrains.net/display/YTD2/Import+Users)
            Example: importUsers([{'login':'vadim', 'fullName':'vadim', 'email':'eee@ss.com', 'jabber':'fff@fff.com'},
                                  {'login':'maxim', 'fullName':'maxim', 'email':'aaa@ss.com', 'jabber':'www@fff.com'}])
        """
        if len(users) <= 0: return

        xml = '<list>\n'
        for u in users:
            xml += '  <user ' + "".join(k + '=' + quoteattr(u[k]) + ' ' for k in u) + '/>\n'
        xml += '</list>'
        print xml
        #TODO: convert response xml into python objects
        return self._reqXml('PUT', '/import/users', xml, 400).toxml()

    def importIssuesXml(self, projectId, assigneeGroup, xml):
        return self._reqXml('PUT', '/import/' + urllib.quote(projectId) + '/issues?' +
                                   urllib.urlencode({'assigneeGroup': assigneeGroup}),
            xml, 400).toxml()

    def importLinks(self, links):
        """ Import links, returns import result (http://confluence.jetbrains.net/display/YTD2/Import+Links)
            Accepts result of getLinks()
            Example: importLinks([{'login':'vadim', 'fullName':'vadim', 'email':'eee@ss.com', 'jabber':'fff@fff.com'},
                                  {'login':'maxim', 'fullName':'maxim', 'email':'aaa@ss.com', 'jabber':'www@fff.com'}])
        """
        xml = '<list>\n'
        for l in links:
            # ignore typeOutward and typeInward returned by getLinks()
            xml += '  <link ' + "".join(attr + '=' + quoteattr(l[attr]) +
                                        ' ' for attr in l if attr not in ['typeInward', 'typeOutward']) + '/>\n'
        xml += '</list>'
        print xml
        #TODO: convert response xml into python objects
        res = self._reqXml('PUT', '/import/links', xml, 400)
        return res.toxml() if hasattr(res, "toxml") else res

    def importIssues(self, projectId, assigneeGroup, issues):
        """ Import issues, returns import result (http://confluence.jetbrains.net/display/YTD2/Import+Issues)
            Accepts retrun of getIssues()
            Example: importIssues([{'numberInProject':'1', 'summary':'some problem', 'description':'some description', 'priority':'1',
                                    'fixedVersion':['1.0', '2.0'],
                                    'comment':[{'author':'yamaxim', 'text':'comment text', 'created':'1267030230127'}]},
                                   {'numberInProject':'2', 'summary':'some problem', 'description':'some description', 'priority':'1'}])
        """
        if len(issues) <= 0:
            return

        xml = '<issues>\n'
        issue_records = dict([])
        for issue in issues:
            record = ""
            record += '  <issue>\n'

            comments = None
            if getattr(issue, "getComments", None):
                comments = issue.getComments()

            for issueAttr in issue:
                attrValue = issue[issueAttr]
                if attrValue is None:
                    continue
                if issueAttr == 'comments':
                    comments = attrValue
                else:
                    # ignore bad fields from getIssue()
                    if issueAttr not in ['id', 'projectShortName', 'votes', 'commentsCount', 'historyUpdated',
                                         'updatedByFullName', 'reporterFullName', 'links', 'attachments', 'jiraId']:
                        record += '    <field name="' + issueAttr + '">\n'
                        if isinstance(attrValue, list) or getattr(attrValue, '__iter__', False):
                            record += "".join('      <value>' + escape(v) + '</value>\n' for v in attrValue)
                        else:
                            record += '      <value>' + escape(attrValue) + '</value>\n'
                        record += '    </field>\n'

            if comments:
                for comment in comments:
                    record += '    <comment ' + "".join(
                        ca + '=' + quoteattr(comment[ca]) + ' ' for ca in comment) + '/>\n'

            record += '  </issue>\n'
            xml += record
            issue_records[issue.numberInProject] = record

        xml += '</issues>'

        #print xml
        #TODO: convert response xml into python objects

        if isinstance(xml, unicode):
            xml = xml.encode('utf-8')

        url = '/import/' + urllib.quote(projectId) + '/issues?' + urllib.urlencode({'assigneeGroup': assigneeGroup})
        if isinstance(url, unicode):
            url = url.encode('utf-8')
        response = self._reqXml('PUT', url, xml, 400).toxml().encode('utf-8')
        item_elements = minidom.parseString(response).getElementsByTagName("item")
        if len(item_elements) != len(issues):
            print response
        else:
            for item in item_elements:
                id = item.attributes["id"].value
                imported = item.attributes["imported"].value.lower()
                if imported == "true":
                    print "Issue [ %s-%s ] imported successfully" % (projectId, id)
                else:
                    print ""
                    print "Failed to import issue [ %s-%s ]." % (projectId, id)
                    print "Reason : "
                    print item.toxml()
                    print "Request was :"
                    print issue_records[id].encode('utf-8')
                print ""
        return response

    def getProject(self, projectId):
        """ http://confluence.jetbrains.net/display/YTD2/GET+project
        """
        return youtrack.Project(self._get("/admin/project/" + urllib.quote(projectId)), self)

    def getProjectIds(self):
        response, content = self._req('GET', '/admin/project/')
        xml = minidom.parseString(content)
        return [e.getAttribute('id') for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def getProjectAssigneeGroups(self, projectId):
        response, content = self._req('GET', '/admin/project/' + urllib.quote(projectId) + '/assignee/group')
        xml = minidom.parseString(content)
        return [youtrack.Group(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def getGroup(self, name):
        return youtrack.Group(self._get("/admin/group/" + urllib.quote(name.encode('utf-8'))), self)

    def getGroups(self):
        response, content = self._req('GET', '/admin/group')
        xml = minidom.parseString(content)
        return [youtrack.Group(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def deleteGroup(self, name):
        return self._req('DELETE', "/admin/group/" + urllib.quote(name.encode('utf-8')))

    def getUserGroups(self, userName):
        response, content = self._req('GET', '/admin/user/%s/group' % urllib.quote(userName.encode('utf-8')))
        xml = minidom.parseString(content)
        return [youtrack.Group(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def setUserGroup(self, user_name, group_name):
        encoded_user_name = urllib.quote(user_name.encode('utf-8'))
        encoded_group_name = urllib.quote(group_name.encode('utf-8'))
        response, content = self._req('POST', '/admin/user/%s/group/%s' % (encoded_user_name, encoded_group_name), body='')
        return response

    def createGroup(self, group):
        content = self._put(
            '/admin/group/%s?autoJoin=false' % group.name.replace(' ', '%20'))
        return content

    def addUserRoleToGroup(self, group, userRole):
        url_group_name = urllib.quote(group.name)
        url_role_name = urllib.quote(userRole.name)
        response, content = self._req('PUT', '/admin/group/%s/role/%s' % (url_group_name, url_role_name), body=userRole.toXml())
        return content

    def getRole(self, name):
        return youtrack.Role(self._get("/admin/role/" + urllib.quote(name)), self)

    def getRoles(self):
        response, content = self._req('GET', '/admin/role')
        xml = minidom.parseString(content)
        return [youtrack.Role(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def getGroupRoles(self, group_name):
        response, content = self._req('GET', '/admin/group/%s/role' % urllib.quote(group_name))
        xml = minidom.parseString(content)
        return [youtrack.UserRole(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def createRole(self, role):
        url_role_name = urllib.quote(role.name)
        url_role_dscr = urllib.quote(role.description) if hasattr(role, 'description') else ''
        content = self._put('/admin/role/%s?description=%s' % (url_role_name, url_role_dscr))
        return content

    def changeRole(self, role, new_name, new_description):
        url_role_name = urllib.quote(role.name)
        url_new_name = urllib.quote(new_name)
        url_new_dscr = urllib.quote(new_description)
        content = self._req('POST', '/admin/role/%s?newName=%s&description=%s' % (url_role_name, url_new_name, url_new_dscr))
        return content

    def addPermissionToRole(self, role, permission):
        url_role_name = urllib.quote(role.name)
        url_prm_name = urllib.quote(permission.name)
        content = self._req('POST', '/admin/role/%s/permission/%s' % (url_role_name, url_prm_name))
        return content

    def getRolePermissions(self, role):
        response, content = self._req('GET', '/admin/role/%s/permission' % urllib.quote(role.name))
        xml = minidom.parseString(content)
        return [youtrack.Permission(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def getPermissions(self):
        response, content = self._req('GET', '/admin/permission')
        xml = minidom.parseString(content)
        return [youtrack.Permission(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def getSubsystem(self, projectId, name):
        response, content = self._req('GET', '/admin/project/' + projectId + '/subsystem/' + urllib.quote(name))
        xml = minidom.parseString(content)
        return youtrack.Subsystem(xml, self)

    def getSubsystems(self, projectId):
        response, content = self._req('GET', '/admin/project/' + projectId + '/subsystem')
        xml = minidom.parseString(content)
        return [youtrack.Subsystem(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def getVersions(self, projectId):
        response, content = self._req('GET', '/admin/project/' + urllib.quote(projectId) + '/version?showReleased=true')
        xml = minidom.parseString(content)
        return [self.getVersion(projectId, v.getAttribute('name')) for v in
                xml.documentElement.getElementsByTagName('version')]

    def getVersion(self, projectId, name):
        return youtrack.Version(
            self._get("/admin/project/" + urllib.quote(projectId) + "/version/" + urllib.quote(name)), self)

    def getBuilds(self, projectId):
        response, content = self._req('GET', '/admin/project/' + urllib.quote(projectId) + '/build')
        xml = minidom.parseString(content)
        return [youtrack.Build(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]


    def getUsers(self, params=dict([])):
        first = True
        users = []
        position = 0
        user_search_params = urllib.urlencode(params)
        while True:
            response, content = self._req('GET', "/admin/user/?start=%s&%s" % (str(position), user_search_params))
            position += 10
            xml = minidom.parseString(content)
            newUsers = [youtrack.User(e, self) for e in xml.documentElement.childNodes if
                        e.nodeType == Node.ELEMENT_NODE]
            if not len(newUsers): return users
            users += newUsers


    def getUsersTen(self, start):
        response, content = self._req('GET', "/admin/user/?start=%s" % str(start))
        xml = minidom.parseString(content)
        users = [youtrack.User(e, self) for e in xml.documentElement.childNodes if
                    e.nodeType == Node.ELEMENT_NODE]
        return users

    def deleteUser(self, login):
        return self._req('DELETE', "/admin/user/" + urllib.quote(login.encode('utf-8')))

    # TODO this function is deprecated
    def createBuild(self):
        raise NotImplementedError

    # TODO this function is deprecated
    def createBuilds(self):
        raise NotImplementedError

    def createProject(self, project):
        return self.createProjectDetailed(project.id, project.name, project.description, project.lead)

    def createProjectDetailed(self, projectId, name, description, projectLeadLogin, startingNumber=1):
        return self._put('/admin/project/' + projectId + '?' +
                         urllib.urlencode({'projectName': name,
                                           'description': description + ' ',
                                           'projectLeadLogin': projectLeadLogin,
                                           'lead': projectLeadLogin,
                                           'startingNumber': str(startingNumber)}))

    # TODO this function is deprecated
    def createSubsystems(self, projectId, subsystems):
        """ Accepts result of getSubsystems()
        """

        for s in subsystems:
            self.createSubsystem(projectId, s)

    # TODO this function is deprecated
    def createSubsystem(self, projectId, s):
        return self.createSubsystemDetailed(projectId, s.name, s.isDefault,
            s.defaultAssignee if s.defaultAssignee != '<no user>' else '')

    # TODO this function is deprecated
    def createSubsystemDetailed(self, projectId, name, isDefault, defaultAssigneeLogin):
        self._put('/admin/project/' + projectId + '/subsystem/' + urllib.quote(name.encode('utf-8')) + "?" +
                  urllib.urlencode({'isDefault': str(isDefault),
                                    'defaultAssignee': defaultAssigneeLogin}))

        return 'Created'

    # TODO this function is deprecated
    def deleteSubsystem(self, projectId, name):
        return self._reqXml('DELETE', '/admin/project/' + projectId + '/subsystem/' + urllib.quote(name.encode('utf-8'))
            , '')

    # TODO this function is deprecated
    def createVersions(self, projectId, versions):
        """ Accepts result of getVersions()
        """

        for v in versions:
            self.createVersion(projectId, v)

    # TODO this function is deprecated
    def createVersion(self, projectId, v):
        return self.createVersionDetailed(projectId, v.name, v.isReleased, v.isArchived, releaseDate=v.releaseDate,
            description=v.description)

    # TODO this function is deprecated
    def createVersionDetailed(self, projectId, name, isReleased, isArchived, releaseDate=None, description=''):
        params = {'description': description,
                  'isReleased': str(isReleased),
                  'isArchived': str(isArchived)}
        if releaseDate is not None:
            params['releaseDate'] = str(releaseDate)
        return self._put(
            '/admin/project/' + urllib.quote(projectId) + '/version/' + urllib.quote(name.encode('utf-8')) + "?" +
            urllib.urlencode(params))

    def getIssues(self, projectId, filter, after, max):
        response, content = self._req('GET', '/project/issues/' + urllib.quote(projectId) + "?" +
                                             urllib.urlencode({'after': str(after),
                                                               'max': str(max),
                                                               'filter': filter}))
        xml = minidom.parseString(content)
        return [youtrack.Issue(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def exportIssueLinks(self):
        response, content = self._req('GET', '/export/links')
        xml = minidom.parseString(content)
        return [youtrack.Link(e, self) for e in xml.documentElement.childNodes if e.nodeType == Node.ELEMENT_NODE]

    def executeCommand(self, issueId, command, comment=None, group=None, run_as = None):
        params = {'command': command}

        if comment is not None:
            params['comment'] = comment

        if group is not None:
            params['group'] = group

        if run_as is not None:
            params['runAs'] = run_as

        response, content = self._req('POST', '/issue/' + issueId + "/execute?" +
                                              urllib.urlencode(params), body='')

        return "Command executed"

    def getCustomField(self, name):
        return youtrack.CustomField(self._get("/admin/customfield/field/" + urllib.quote(name.encode('utf-8'))), self)

    def getCustomFields(self):
        response, content = self._req('GET', '/admin/customfield/field')
        xml = minidom.parseString(content)
        return [self.getCustomField(e.getAttribute('name')) for e in xml.documentElement.childNodes if
                e.nodeType == Node.ELEMENT_NODE]

    def createCustomField(self, cf):
        params = dict([])
        if hasattr(cf, "defaultBundle"):
            params["defaultBundle"] = cf.defaultBundle
        if hasattr(cf, "attachBundlePolicy"):
            params["attachBundlePolicy"] = cf.attachBundlePolicy
        auto_attached = False
        if hasattr(cf, "autoAttached"):
            auto_attached = cf.autoAttached
        return self.createCustomFieldDetailed(cf.name, cf.type, cf.isPrivate, cf.visibleByDefault, auto_attached,
            params)

    def createCustomFieldDetailed(self, customFieldName, typeName, isPrivate, defaultVisibility,
                                  auto_attached=False, additional_params=dict([])):
        params = {'type': typeName, 'isPrivate': str(isPrivate), 'defaultVisibility': str(defaultVisibility),
                  'autoAttached': str(auto_attached)}
        params.update(additional_params)
        for key in params:
            if isinstance(params[key], unicode):
                params[key] = params[key].encode('utf-8')

        self._put('/admin/customfield/field/' + urllib.quote(customFieldName.encode('utf-8')) + '?' +
                  urllib.urlencode(params), )

        return "Created"

    def createCustomFields(self, cfs):
        for cf in cfs:
            self.createCustomField(cf)

    def getProjectCustomField(self, projectId, name):
        return youtrack.ProjectCustomField(
            self._get("/admin/project/" + urllib.quote(projectId) + "/customfield/" + urllib.quote(name.encode('utf8')))
            , self)

    def getProjectCustomFields(self, projectId):
        response, content = self._req('GET', '/admin/project/' + urllib.quote(projectId) + '/customfield')
        xml = minidom.parseString(content)
        return [self.getProjectCustomField(projectId, e.getAttribute('name')) for e in
                xml.getElementsByTagName('projectCustomField')]

    def createProjectCustomField(self, projectId, pcf):
        return self.createProjectCustomFieldDetailed(projectId, pcf.name, pcf.emptyText, pcf.params)

    def createProjectCustomFieldDetailed(self, projectId, customFieldName, emptyFieldText, params=None):
        if not len(emptyFieldText.strip()):
            emptyFieldText = u"No " + customFieldName
        _params = {'emptyFieldText': emptyFieldText}
        if params is not None:
            _params.update(params)
        for key in _params:
            if isinstance(_params[key], unicode):
                _params[key] = _params[key].encode('utf-8')
        return self._put(
            '/admin/project/' + projectId + '/customfield/' + urllib.quote(customFieldName.encode('utf-8')) + '?' +
            urllib.urlencode(_params))

    def deleteProjectCustomField(self, project_id, pcf_name):
        self._req('DELETE', '/admin/project/' + urllib.quote(project_id) + "/customfield/" + urllib.quote(pcf_name))

    def getIssueLinkTypes(self):
        response, content = self._req('GET', '/admin/issueLinkType')
        xml = minidom.parseString(content)
        return [youtrack.IssueLinkType(e, self) for e in xml.getElementsByTagName('issueLinkType')]

    def createIssueLinkTypes(self, issueLinkTypes):
        for ilt in issueLinkTypes:
            return self.createIssueLinkType(ilt)

    def createIssueLinkType(self, ilt):
        return self.createIssueLinkTypeDetailed(ilt.name, ilt.outwardName, ilt.inwardName, ilt.directed)

    def createIssueLinkTypeDetailed(self, name, outwardName, inwardName, directed):
        return self._put('/admin/issueLinkType/' + urllib.quote(name) + '?' +
                         urllib.urlencode({'outwardName': outwardName,
                                           'inwardName': inwardName,
                                           'directed': directed}))

    def getAllBundles(self, field_type):
        field_type = self.get_field_type(field_type)
        if field_type == "enum":
            tag_name = "enumFieldBundle"
        elif field_type == "user":
            tag_name = "userFieldBundle"
        else:
            tag_name = self.bundle_paths[field_type]
        names = [e.getAttribute("name") for e in self._get('/admin/customfield/' +
                                                           self.bundle_paths[field_type]).getElementsByTagName(
            tag_name)]
        return [self.getBundle(field_type, name) for name in names]


    def get_field_type(self, field_type):
        if "[" in field_type:
            field_type = field_type[0:-3]
        return field_type

    def getBundle(self, field_type, name):
        field_type = self.get_field_type(field_type)
        response = self._get('/admin/customfield/%s/%s' % (self.bundle_paths[field_type],
                                                           urllib.quote(name.encode('utf-8'))))
        return self.bundle_types[field_type](response, self)

    def renameBundle(self, bundle, new_name):
        response, content = self._req("POST", "/admin/customfield/%s/%s?newName=%s" % (
            self.bundle_paths[bundle.get_field_type()], bundle.name, new_name), "", ignoreStatus=301)
        return response

    def createBundle(self, bundle):
        return self._reqXml('PUT', '/admin/customfield/' + self.bundle_paths[bundle.get_field_type()],
            body=bundle.toXml(), ignoreStatus=400)

    def deleteBundle(self, bundle):
        response, content = self._req("DELETE", "/admin/customfield/%s/%s" % (
            self.bundle_paths[bundle.get_field_type()], bundle.name), "")
        return response

    def addValueToBundle(self, bundle, value):
        request = ""
        if bundle.get_field_type() != "user":
            request = "/admin/customfield/%s/%s/" % (
                self.bundle_paths[bundle.get_field_type()], urllib.quote(bundle.name.encode('utf-8')))
            if isinstance(value, str):
                request += urllib.quote(value, safe="")
            elif isinstance(value, unicode):
                request += urllib.quote(value.encode('utf-8'), safe="")
            else:
                request += urllib.quote(value.name.encode('utf-8'), safe="") + "?"
                params = dict()
                for e in value:
                    if (e != "name") and (e != "element_name") and len(value[e]):
                        params[e] = value[e]
                if len(params):
                    request += urllib.urlencode(params)
        else:
            request = "/admin/customfield/userBundle/%s/" % urllib.quote(bundle.name.encode('utf-8'))
            if isinstance(value, youtrack.User):
                request += "individual/%s/" % value.login
            elif isinstance(value, youtrack.Group):
                request += "group/%s/" % urllib.quote(value.name.encode('utf-8'))
            else:
                request += "individual/%s/" % value
        return self._put(request)

    def removeValueFromBundle(self, bundle, value):
        field_type = bundle.get_field_type()
        request = "/admin/customfield/%s/%s/" % (self.bundle_paths[field_type], bundle.name)
        if field_type != "user":
            request += urllib.quote(value.name)
        elif isinstance(value, youtrack.User):
            request += "individual/" + urllib.quote(value.login)
        else:
            request += "group/" + value.name
        response, content = self._req("DELETE", request, "", ignoreStatus=204)
        return response


    def getEnumBundle(self, name):
        return youtrack.EnumBundle(self._get("/admin/customfield/bundle/" + urllib.quote(name)), self)


    def createEnumBundle(self, eb):
        return self.createBundle(eb)

    def deleteEnumBundle(self, name):
        return self.deleteBundle(self.getEnumBundle(name))

    def createEnumBundleDetailed(self, name, values):
        xml = '<enumeration name=\"' + name.encode('utf-8') + '\">'
        xml += ' '.join('<value>' + v + '</value>' for v in values)
        xml += '</enumeration>'
        return self._reqXml('PUT', '/admin/customfield/bundle', body=xml.encode('utf8'), ignoreStatus=400)

    def addValueToEnumBundle(self, name, value):
        return self.addValueToBundle(self.getEnumBundle(name), value)

    def addValuesToEnumBundle(self, name, values):
        return ", ".join(self.addValueToEnumBundle(name, value) for value in values)


    bundle_paths = {
        "enum": "bundle",
        "build": "buildBundle",
        "ownedField": "ownedFieldBundle",
        "state": "stateBundle",
        "version": "versionBundle",
        "user": "userBundle"
    }

    bundle_types = {
        "enum": lambda xml, yt: youtrack.EnumBundle(xml, yt),
        "build": lambda xml, yt: youtrack.BuildBundle(xml, yt),
        "ownedField": lambda xml, yt: youtrack.OwnedFieldBundle(xml, yt),
        "state": lambda xml, yt: youtrack.StateBundle(xml, yt),
        "version": lambda xml, yt: youtrack.VersionBundle(xml, yt),
        "user": lambda xml, yt: youtrack.UserBundle(xml, yt)
    }



    