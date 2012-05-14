FIELD_TYPES = {
    u'java.lang.String': 'string',
    u'java.util.Date': 'date',
    u'com.atlassian.jira.project.version.Version': 'version[*]',
    u'com.atlassian.jira.issue.issuetype.IssueType': 'enum[1]',
    u'com.atlassian.jira.issue.priority.Priority': 'enum[1]',
    u'com.atlassian.jira.issue.status.Status': 'state[1]',
    u'com.opensymphony.user.User': 'user[1]',
    u'com.atlassian.jira.bc.project.component.ProjectComponent': 'ownedField[*]',
    u'com.atlassian.jira.plugin.system.customfieldtypes:importid': 'string',
    u'com.atlassian.jira.plugin.system.customfieldtypes:radiobuttons': 'enum[1]',
    u'com.atlassian.jira.toolkit:multikeyfield': 'enum[*]',
    u'com.atlassian.jira.toolkit:participants': 'user[*]',
    u'com.atlassian.jira.plugin.system.customfieldtypes:multicheckboxes': 'enum[*]',
    u'com.atlassian.jira.plugin.system.customfieldtypes:textfield': 'string'
}

FIELD_NAMES = {
    u'reporter': 'reporterName',
    u'fixVersions': 'Fix versions',
    u'versions': 'Affected versions',
    u'status' : 'State',
    u'issuetype' : 'Type'
}

EXISTING_FIELDS = ['numberInProject', 'projectShortName', 'summary', 'description', 'created',
                   'updated', 'updaterName', 'resolved', 'reporterName']

class JiraException(Exception):
    def __init__(self, *args, **kwargs):
        super(JiraException, self).__init__(*args, **kwargs)
