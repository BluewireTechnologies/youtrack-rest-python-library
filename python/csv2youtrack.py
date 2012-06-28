import calendar
import re
import time
import datetime
import csvClient
from csvClient.client import Client
import csvClient.youtrackMapping
import youtrack

csvClient.FIELD_TYPES.update(youtrack.EXISTING_FIELD_TYPES)
from youtrack import YouTrackException, Issue, User, Comment
from youtrack.connection import Connection
from youtrack.importHelper import create_custom_field


def main():
    source_file = "/home/user/src.csv"
    target_url = "http://localhost:8081"
    target_login = "root"
    target_password = "root"

    csv2youtrack(source_file, target_url, target_login, target_password)


def get_projects(issues):
    return list(set([get_project(issue) for issue in issues]))


def get_project(issue):
    for key, value in csvClient.FIELD_NAMES.items():
        if value == "project":
            return re.sub(r'\W+', "", issue[key])

def import_custom_fields(field_names, target):
    for name in field_names:
        yt_name = get_yt_field_name(name)
        yt_type = get_yt_field_type(yt_name)
        if (yt_type is not None) and (yt_name not in youtrack.EXISTING_FIELDS):
            create_custom_field(target, yt_type, yt_name, True)


def import_user(target, user):
    yt_user = User()
    yt_user.login = user
    yt_user.email = user
    target.importUsers([yt_user])


def add_value_to_field(target, project, yt_field_name, yt_field_type, yt_field_value):
    if yt_field_type.find("[") == -1:
        return
    if yt_field_type.find("user") != -1:
        import_user(target, yt_field_value)
    if yt_field_name in youtrack.EXISTING_FIELDS:
        return
    bundle = target.getBundle(yt_field_type, target.getProjectCustomField(project, yt_field_name).bundle)
    try:
        target.addValueToBundle(bundle, yt_field_value)
    except YouTrackException:
        pass


def to_yt_issue(issue, target):
    yt_issue = Issue()
    project = get_project(issue)
    for key, value in issue.items():
        if key != "comments":
            field_name = get_yt_field_name(key)
            if field_name == "numberInProject":
                number_regex = re.compile("\d+")
                match_result = number_regex.search(value)
                yt_issue["numberInProject"] = match_result.group()
                continue
            field_type = get_yt_field_type(field_name)
            if field_type is not None:
                field_value = get_yt_field_value(field_name, field_type, value)
                if field_value is not None:
                    if isinstance(field_value, list):
                        for elem in field_value:
                            add_value_to_field(target, project, field_name, field_type, elem)
                    else:
                        add_value_to_field(target, project, field_name, field_type, field_value)
                    yt_issue[field_name] = field_value

    if not hasattr(yt_issue, "reporterName"):
        yt_issue.reporterName = "guest"
    yt_issue.comments = [to_yt_comment(yt_issue.reporterName, comment) for comment in issue["comments"]]
    return yt_issue


def to_yt_comment(reporter, comment_string):
    comment = Comment()
    comment.author = reporter
    comment.text = comment_string
    comment.created = str(int(time.time() * 1000))
    return comment


def get_yt_field_name(field_name):
    if field_name in csvClient.FIELD_NAMES:
        return csvClient.FIELD_NAMES[field_name]
    return field_name


def get_yt_field_type(yt_field_name):
    if yt_field_name in csvClient.FIELD_TYPES:
        return csvClient.FIELD_TYPES[yt_field_name]
    return None


def get_yt_field_value(field_name, field_type, value):
    if field_type == "date":
        return to_unix_date(value)
    if field_type.find("user") != -1:
        return value.replace(" ", "_")
    return value


def to_unix_date(date):
    if csvClient.DATE_FORMAT_STRING[-2:] == "%z":
        dt = datetime.datetime.strptime(date[:-6], csvClient.DATE_FORMAT_STRING[:-2])
    else:
        dt = datetime.datetime.strptime(date, csvClient.DATE_FORMAT_STRING)
    return str(calendar.timegm(dt.timetuple()) * 1000)


def csv2youtrack(source_file, target_url, target_login, target_password):
    target = Connection(target_url, target_login, target_password)
    source = Client(source_file)

    import_custom_fields(source.get_header(), target)

    max = 100
    while True:
        issues = source.get_issue_list(max)
        if not len(issues):
            break
        projects = get_projects(issues)
        for p in projects:
            try:
                target.getProject(p)
            except YouTrackException:
                target.createProjectDetailed(p, p, "", target_login)

            target.importIssues(p, p + " Assignees", [to_yt_issue(issue, target)
                                                      for issue in issues if (get_project(issue) == p)])


if __name__ == "__main__":
    main()