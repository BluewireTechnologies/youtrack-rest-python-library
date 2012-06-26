import HTMLParser
import calendar
import re
from urllib import unquote
import urllib
import urllib2
import xml
import datetime
import sys
import gdata.projecthosting.client
import gdata.projecthosting.data
import gdata.gauth
import gdata.client
import gdata.data

import googleCode
import googleCode.spock
from youtrack import YouTrackException, Issue, Comment
from youtrack.connection import Connection
from youtrack.importHelper import create_bundle_safe

def main():
    source_login, source_password, target_url, target_login, target_password, project_name, project_id = sys.argv[1:]
    googlecode2youtrack(project_name, source_login, source_password, target_url, target_login, target_password,
        project_id)


def create_and_attach_custom_field(target, project_id, field_name, field_type):
    normalized_name = field_name.lower()
    if normalized_name not in [field.name.lower() for field in target.getProjectCustomFields(project_id)]:
        if normalized_name not in [field.name.lower() for field in target.getCustomFields()]:
            target.createCustomFieldDetailed(field_name, field_type, False, True)
        if field_type in ["integer", "string", "date"]:
            target.createProjectCustomFieldDetailed(project_id, field_name, "No " + field_name)
        else:
            bundle_name = field_name + " bundle"
            create_bundle_safe(target, bundle_name, field_type)
            target.createProjectCustomFieldDetailed(project_id, field_name, "No " + field_name, {"bundle": bundle_name})


def add_value_to_field(target, project_id, field_name, field_type, value):
    if field_type.startswith("user"):
        create_user(target, value)
    if field_type in ["integer", "string", "date"]:
        return
    project_field = target.getProjectCustomField(project_id, field_name)
    bundle = target.getBundle(field_type, project_field.bundle)
    try:
        target.addValueToBundle(bundle, value)
    except YouTrackException:
        pass


def create_user(target, value):
    email = value if (value.find("@") != -1) else (value + "@gmail.com")
    try:
        target.createUserDetailed(value, value, email, email)
    except YouTrackException:
        pass


def to_unix_date(dt_str):
    dt, _, us = dt_str.partition(".")
    dt = datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    us = int(us.rstrip("Z"), 10)
    res = dt + datetime.timedelta(microseconds=us)
    return str(calendar.timegm(res.timetuple()) * 1000)


def get_yt_field_name(g_field_name):
    if g_field_name in googleCode.FIELD_NAMES:
        return googleCode.FIELD_NAMES[g_field_name]
    return g_field_name


def get_custom_field_values(g_issue):
    labels = [label.text for label in g_issue.label]
    values = {}
    for label in labels:
        if "-" not in label:
            continue
        name, value = label.split("-", 1)
        yt_name = get_yt_field_name(name)
        if yt_name in googleCode.FIELD_TYPES:
            if yt_name in values:
                values[yt_name].append(value)
            else:
                values[yt_name] = [value]
    return values


def to_yt_comment(target, comment):
    yt_comment = Comment()
    yt_comment.author = comment.author[0].name.text
    create_user(target, yt_comment.author)
    if comment.content.text is None:
        return None
    yt_comment.text = comment.content.text.encode('utf-8')
    yt_comment.created = to_unix_date(comment.published.text)
    return yt_comment


def to_yt_issue(target, project_id, g_issue, g_comments):
    issue = Issue()
    issue.numberInProject = issue_id(g_issue)
    issue.summary = g_issue.title.text.encode('utf-8')
    issue.description = HTMLParser.HTMLParser().unescape(g_issue.content.text).replace("<b>", "*").replace("</b>", "*").encode('utf-8')
#    issue.description = g_issue.content.text.encode('utf-8')
    issue.created = to_unix_date(g_issue.published.text)
    issue.updated = to_unix_date(g_issue.updated.text)
    reporter = g_issue.author[0].name.text
    create_user(target, reporter)
    issue.reporterName = reporter
    assignee = g_issue.owner.username.text if hasattr(g_issue, "owner") and (g_issue.owner is not None) else None
    assignee_field_name = get_yt_field_name("owner")
    if assignee is not None:
        add_value_to_field(target, project_id, assignee_field_name, googleCode.FIELD_TYPES[assignee_field_name],
            assignee)
        issue[assignee_field_name] = assignee
    status_field_name = get_yt_field_name("status")
    status = g_issue.status.text if hasattr(g_issue, "status") and (g_issue.status is not None) else None
    if status is not None:
        add_value_to_field(target, project_id, status_field_name, googleCode.FIELD_TYPES[status_field_name], status)
        issue[status_field_name] = status

    for field_name, field_value in get_custom_field_values(g_issue).items():
        for value in field_value:
            add_value_to_field(target, project_id, field_name, googleCode.FIELD_TYPES[field_name], value)
        issue[field_name] = field_value

    issue.comments = []
    for comment in g_comments:
        yt_comment = to_yt_comment(target, comment)
        if yt_comment is not None:
            issue.comments.append(yt_comment)

    return issue


def get_tags(issue):
    return [label.text for label in issue.label if
            get_yt_field_name(label.text.split("-")[0]) not in googleCode.FIELD_TYPES.keys()]


def import_tags(target, project_id, issue):
    for tag in get_tags(issue):
        try:
            target.executeCommand(project_id + "-" + issue_id(issue), "tag " + tag)
        except YouTrackException, e:
            print str(e)


def get_issue_href(issue):
    return filter(lambda l: l.rel == 'alternate', issue.link)[0].href


def issue_id(i):
    return i.get_elements(tag='id', namespace='http://schemas.google.com/projecthosting/issues/2009')[0].text


def get_attachments(projectName, issue):
    content = urllib.urlopen(get_issue_href(issue)).read()

    attach = re.compile(
        '<a href="(http://' + projectName + '\.googlecode\.com/issues/attachment\?aid=\S+name=(\S+)&\S+)">Download</a>')

    res = []
    for m in attach.finditer(content):
        res.append((xml.sax.saxutils.unescape(m.group(1)), m.group(2)))

    return res


def import_attachments(target, project_id, project_name, issue, author_login):
    for (url, name) in get_attachments(project_name, issue):
        print "  Transfer attachment [" + name + "]"
        try:
            content = urllib2.urlopen(urllib2.Request(url))
        except:
            print "Unable to import attachment [ " + name + " ] for issue [ " + issue_id(issue) + " ]"
            continue
        print target.createAttachment(project_id + "-" + issue_id(issue), unquote(name).decode('utf-8'), content,
            author_login,
            contentLength=int(content.headers.dict['content-length']),
            #contentType=content.info().type, octet/stream always :(
            created=None,
            group=None)


def googlecode2youtrack(project_name, source_login, source_password, target_url, target_login, target_password,
                        project_id):
    target = Connection(target_url, target_login, target_password)

    try:
        target.getProject(project_id)
    except YouTrackException:
        target.createProjectDetailed(project_id, project_name, "", target_login)

    for field_name, field_type in googleCode.FIELD_TYPES.items():
        create_and_attach_custom_field(target, project_id, field_name, field_type)

    start = 1
    max = 30

    while True:
        source = gdata.projecthosting.client.ProjectHostingClient()
        source.client_login(source_login, source_password, source="youtrack", service="code")
        print "Get issues from " + str(start) + " to " + str(start + max)
        query = gdata.projecthosting.client.Query(start_index=start, max_results=max)
        issues = source.get_issues(project_name, query=query).entry
        start += max

        if len(issues) <= 0:
            break

        target.importIssues(project_id, project_name + " assignees",
            [to_yt_issue(target, project_id, issue, source.get_comments(project_name, issue_id(issue)).entry) for issue
             in issues])
        for issue in issues:
            import_tags(target, project_id, issue)
            import_attachments(target, project_id, project_name, issue, target_login)


if __name__ == "__main__":
    main()