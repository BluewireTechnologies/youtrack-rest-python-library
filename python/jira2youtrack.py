import calendar
import sys
import datetime
import urllib
import urllib2
import jira
from jira.client import JiraClient
from youtrack import Issue, YouTrackException, Comment, Link
from youtrack.connection import Connection
from youtrack.importHelper import create_bundle_safe

jt_fields = []

def main():
    #source_url, source_login, source_password, target_url, target_login, target_password, project_id = sys.argv[1:8]
    source_url = "http://jira.codehaus.org"
    source_login = "anna.zhdan"
    source_password = "94829482"
    target_url = "http://localhost:8081"
    target_login = "root"
    target_password = "root"
    project_id = "GROOVY"
    jira2youtrack(source_url, source_login, source_password, target_url, target_login, target_password, project_id)

#    print("Usage: jira2youtrack.py source_url source_login source_password "
#          " target_url target_login target_password project_id")



def create_yt_issue_from_jira_issue(target, issue, project_id):
    yt_issue = Issue()
    yt_issue['comments'] = []
    yt_issue.numberInProject = issue['key'][(issue['key'].find('-') + 1):]
    for field in issue['fields'].values():
        field_type = get_yt_field_type(field[u'type'])
        field_name = get_yt_field_name(field[u'name'])
        if field_name == 'comment':
            for comment in field['value']:
                yt_comment = Comment()
                yt_comment.text = comment['body']
                comment_author_name = "guest"
                if 'author' in comment:
                    comment_author = comment['author']
                    create_user(target, comment_author)
                    comment_author_name = comment_author['name']
                yt_comment.author = comment_author_name.replace(' ', '_')
                yt_comment.created = to_unix_date(comment['created'])
                yt_comment.updated = to_unix_date(comment['updated'])
                yt_issue['comments'].append(yt_comment)

        elif (field_name is not None) and (field_type is not None):
            if 'value' in field:
                value = field['value']
                if len(value):
                    if isinstance(value, list):
                        yt_issue[field_name] = []
                        for v in value:
                            create_value(target, v, field_name, field_type, project_id)
                            yt_issue[field_name].append(get_value_presentation(field_type, v))
                    else:
                        create_value(target, value, field_name, field_type, project_id)
                        yt_issue[field_name] = get_value_presentation(field_type, value)
    return yt_issue


def process_labels(target, issue):
    tags = issue['fields']['labels']['value']
    for tag in tags:
    #        tag = tag.replace(' ', '_')
    #        tag = tag.replace('-', '_')
        try:
            target.executeCommand(issue['key'], 'tag ' + tag)
        except YouTrackException:
            try:
                target.executeCommand(issue['key'], ' tag ' + tag.replace(' ', '_').replace('-', '_'))
            except YouTrackException, e:
                print(str(e))


def get_yt_field_name(jira_name):
    if jira_name in jira.FIELD_NAMES:
        return jira.FIELD_NAMES[jira_name]
    return jira_name


def get_yt_field_type(jira_type):
    if jira_type in jira.FIELD_TYPES:
        return jira.FIELD_TYPES[jira_type]
    return None


def process_links(target, issue, yt_links):
    links = issue['fields']['links']['value'] + issue['fields']['sub-tasks']['value']
    for link in links:
        is_directed = 'direction' in link
        target_issue = issue['key']
        source_issue = link['issueKey']

        try:
            if int(target_issue[6:]) > int(source_issue[6:]):
                continue
        except:
            continue

        try:
            link_description = link['type']['description'] if 'description' in link['type'] else link['type']['name']
            if is_directed:
                target.createIssueLinkTypeDetailed(link['type']['name'], link_description, link_description, False)
            else:
                outward = 'is ' + link['type']['name']
                inward = link_description
                if link['type']['direction'] == u'OUTBOUND':
                    c = outward
                    outward = inward
                    inward = outward
                    c = source_issue
                    source_issue = target_issue
                    target_issue = c
                target.createIssueLinkTypeDetailed(link['type']['name'], outward, inward, True)
        except YouTrackException:
            pass
        yt_link = Link()
        yt_link.typeName = link['type']['name']
        yt_link.source = source_issue
        yt_link.target = target_issue
        yt_links.append(yt_link)


def create_user(target, value):
    try:
        target.createUserDetailed(value['name'].replace(' ', '_'), value['displayName'], 'fare_email', 'fake_jabber')
    except YouTrackException, e:
        print(str(e))


def create_value(target, value, field_name, field_type, project_id):
    if field_type.startswith('user'):
        create_user(target, value)
        value['name'] = value['name'].replace(' ', '_')
    if field_name in jira.EXISTING_FIELDS:
        return
    if field_name.lower() not in [field.name.lower() for field in target.getProjectCustomFields(project_id)]:
        if field_name.lower() not in [field.name.lower() for field in target.getCustomFields()]:
            target.createCustomFieldDetailed(field_name, field_type, False, True, False, {})
        if field_type in ['string', 'date', 'integer']:
            target.createProjectCustomFieldDetailed(project_id, field_name, "No " + field_name)
        else:
            bundle_name = field_name + " bundle"
            create_bundle_safe(target, bundle_name, field_type)
            target.createProjectCustomFieldDetailed(project_id, field_name, "No " + field_name, {'bundle': bundle_name})
    if field_type in ['string', 'date', 'integer']:
        return
    project_field = target.getProjectCustomField(project_id, field_name)
    bundle = target.getBundle(field_type, project_field.bundle)
    try:
        if 'name' in value:
            target.addValueToBundle(bundle, value['name'])
        elif 'value' in value:
            target.addValueToBundle(bundle, value['value'])
    except YouTrackException:
        pass


def to_unix_date(time_string):
    time = time_string[:time_string.rfind('.')].replace('T', ' ')
    time_zone = time_string[-5:]
    tz_diff = 1
    if time_zone[0] == '-':
        tz_diff = -1
    tz_diff *= (int(time_zone[1:3]) * 60 + int(time_zone[3:5]))
    dt = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
    return str((calendar.timegm(dt.timetuple()) + tz_diff) * 1000)


def get_value_presentation(field_type, value):
    if field_type == 'date':
        return to_unix_date(value)
    if field_type == 'integer':
        return str(value)
    if field_type == 'string':
        return value
    if 'name' in value:
        return value['name']
    if 'value' in value:
        return value['value']


def process_attachments(source, target, issue):
    for attach in issue['fields']['attachment']['value']:
        attachment = JiraAttachment(attach, source)
        if 'author' in attach:
            create_user(target, attach['author'])
        target.createAttachmentFromAttachment(issue['key'], attachment)


def jira2youtrack(source_url, source_login, source_password, target_url, target_login, target_password, project_id):
    print("source_url      : " + source_url)
    print("source_login    : " + source_login)
    print("source_password : " + source_password)
    print("target_url      : " + target_url)
    print("target_login    : " + target_login)
    print("target_password : " + target_password)
    print("project_id      : " + project_id)

    source = JiraClient(source_url, source_login, source_password)
    target = Connection(target_url, target_login, target_password)
#
#    target.createProjectDetailed(project_id, project_id, "", target_login)
#
#    for i in range(0, 5500):
#        try:
#            jira_issues = source.get_issues(project_id, i * 10, (i + 1) * 10)
#            target.importIssues(project_id, project_id + " assignees",
#                [create_yt_issue_from_jira_issue(target, issue, project_id) for issue in
#                 jira_issues])
#            for issue in jira_issues:
#                process_labels(target, issue)
#                process_attachments(source, target, issue)
#        except BaseException, e:
#            print(str(e))

    for i in range(0, 5500):
        jira_issues = source.get_issues(project_id, i * 50, (i + 1) * 50)
        links = []
        for issue in jira_issues:
            process_links(target, issue, links)
        print(target.importLinks(links))


class JiraAttachment(object):
    def __init__(self, attach, source):
        self.authorLogin = attach['author']['name'].replace(' ', '_') if 'author' in attach else 'root'
        self._url = attach['content']
        self.name = attach['filename']
        self.created = to_unix_date(attach['created'])
        self._source = source

    def getContent(self):
        return urllib2.urlopen(urllib2.Request(self._url, headers=self._source._headers))

if __name__ == '__main__':
    main()

