from csvClient.client import Client
from youtrack.connection import Connection
from youtrack import YouTrackException
import sys
import csvClient
import csvClient.jrubyJiraMapping
import youtrack
import time
import datetime
import calendar

# issue fields that are already used in YT
YT_ISSUE_FIELDS = ["numberInProject", "summary", "description", "created", "updated", "updaterName", "resolved",
                   "reporterName", "assigneeName", "type", "priority", "state", "subsystem", "affectsVersion",
                   "voterName", "fixedVersion", "permittedGroup", "tags", "fixedInBuild", "watcherName"]

def main() :
    sys.stdout = open("out.txt","w")
    try :
        target_url, target_login, target_password, project_id, project_name, csv_file_path = sys.argv[1:]
    except BaseException, e:
        print e
        sys.exit()
    csv2youtrack(target_url, target_login, target_password, project_id, project_name, csv_file_path)

# you can rewrite this method if you want to extract some
# extra information (f.e. email)  from the user description
def to_yt_user(user_description) :
    user = youtrack.User()
    user.login = user_description.replace(" ", "_")
    user.email = csvClient.DEFAULT_EMAIL
    return user

# we assume that comment_string only contains the text of
# comment (no author name or date of creation)
def to_yt_comment(comment_string) :
    comment = youtrack.Comment()
    comment.author = "guest"
    comment.text = comment_string
    comment.created = str(int(time.time() * 1000))
    return comment

def to_yt_subsystem(subsystem_name) :
    subsys = youtrack.Subsystem()
    subsys.name = subsystem_name.replace("/", "%252F")
    subsys.defaultAssignee = ""
    subsys.isDefault = False
    return subsys

def to_yt_version(version_name) :
    version = youtrack.Version()
    version.name = version_name
    version.releaseDate = str(int(time.time() * 1000))
    version.description = ""
    version.isReleased = True
    version.isArchived = False
    return version




# you need something like this, if date in your csv file has timezone,
# represented like +HH:MM or -HH:MM
#def to_unix_date(time_string) :
#    l = len(time_string)
#    delta = time_string[(l - 6) : l]
#    time_string = time_string[: (l - 6)]
#    dt = datetime.datetime.strptime(time_string, csvClient.DATE_FORMAT_STRING)
#    dt = dt + datetime.timedelta(minutes = int (delta[0] + delta[4:]) + int(delta[:3]) * 60)
#    return str(calendar.timegm(dt.timetuple()) * 1000)

def to_unix_date(time_string) :
    dt = datetime.datetime.strptime(time_string, csvClient.DATE_FORMAT_STRING)
    return str(calendar.timegm(dt.timetuple()) * 1000)

def to_yt_issue(issue) :
    yt_issue = youtrack.Issue()
    yt_issue.comments = []
    for field in issue :
        if field in csvClient.IGNORE_COLUMNS:
            # we don't import value of this field
            continue
        value = issue[field]
        if value == "":
            # if there is no value we do nothing
            continue
        if field in csvClient.IGNORE_VALUES:
            if value == csvClient.IGNORE_VALUES[field]:
                # in current issue this field has the value which we
                # interpret as "NO VALUE"
                continue
        # finding out to which yt issue fields this fields corresponds
        yt_fields = get_keys(field)
        if not len(yt_fields):
            yt_fields.add(field)
        for key in yt_fields :
            if key in ["tags", "comments"]:
                # tags and comments are  imported separately
                continue
            value = get_value(key, value)
            if key in ["created", "updated", "resolved"]:
                # date va;ues should be processed like this
                yt_issue[key] = to_unix_date(value)
            elif key in ["reporterName", "assigneeName"]:
                yt_issue[key] = value.replace(" ", "_")
            elif key == "watcherName":
                yt_issue["watcherName"] = set([])
                watcher_names = value.split(",")
                for name in watcher_names :
                    name = name.strip().replace(" ", "_")
                    if name != "":
                        yt_issue["watcherName"].add(name)
#            # for jira
#            elif (key == "numberInProject") :
#                yt_issue[key]=value.split("-")[1]
#            elif (key == "subsystem") :
#                yt_issue[key] = value.split("/")
#            elif (key in ["fixedVersion", "affectsVersion"]) :
#                yt_issue[key] = value.split("/")
            else :
                yt_issue[key] = value


    # setting default values where needed
    for key in csvClient.DEFAULT_VALUES :
        if not (key in yt_issue) :
            yt_issue[key] = csvClient.DEFAULT_VALUES[key]
        elif yt_issue[key] == "":
            yt_issue[key] = csvClient.DEFAULT_VALUES[key]
    yt_issue.comments = []
    for comment in issue["comments"] :
        if comment != "":
            yt_issue.comments.append(to_yt_comment(comment))
    return yt_issue


def get_field_name(key) :
    if key in csvClient.FIELDS:
        return csvClient.FIELDS[key]
    return key

def get_keys(value) :
    result = set([])
    for key in csvClient.FIELDS :
        if csvClient.FIELDS[key] == value:
            result.add(key)
    return result

def get_value(field_name, value) :
    if field_name in csvClient.VALUES:
        value_map = csvClient.VALUES[field_name]
        if value in value_map:
            return value_map[value]
    return value




def csv2youtrack(target_url, target_login, target_password, project_id, project_name, csv_file_path) :
    print "target_url       :   " + target_url
    print "traget_login     :   " + target_login
    print "target_password  :   " + target_password
    print "project_id       :   " + project_id
    print "project_name     :   " + project_name
    print "csv_file_path    :   " + csv_file_path

    #creating client for file to import issues from
    client = Client(csv_file_path)
    #creating connection to youtrack to import issues in
    target = Connection(target_url, target_login, target_password)

    print "Creating project [ %s ]" % project_name
    try :
        target.getProject(project_id)
    except YouTrackException:
        target.createProjectDetailed(project_id, project_name, "", target_login)

    print "Importing users"
    #getting user names
    # reporters, assignees and watchers mast be registered users
    reporter_field_name = get_field_name("reporterName")
    reporters = client.get_distinct(reporter_field_name)
    if reporter_field_name in csvClient.IGNORE_VALUES:
        ignored_value = csvClient.IGNORE_VALUES[reporter_field_name]
        if ignored_value in reporters:
            reporters.remove(ignored_value)
    assignee_field_name = get_field_name("assigneeName")
    assignees = client.get_distinct(assignee_field_name)
    if assignee_field_name in csvClient.IGNORE_VALUES:
        ignored_value = csvClient.IGNORE_VALUES[assignee_field_name]
        if ignored_value in assignees:
            assignees.remove(ignored_value)
    watcher_field_name = get_field_name("watcherName")
    watcher_fields = client.get_distinct(watcher_field_name)
    watchers = set([])
    for elem in watcher_fields :
        watcher_names = elem.split(",")
        for name in watcher_names :
            watchers.add(name.strip())
    if watcher_field_name in csvClient.IGNORE_VALUES:
        ignored_value = csvClient.IGNORE_VALUES[watcher_field_name]
        if ignored_value in watchers:
            watchers.remove(ignored_value)
    users = reporters | assignees | watchers
    #importing users to yt
    yt_users = list([])
    for usr in users :
        print "Processing user [ %s ]" % usr
        yt_users.append(to_yt_user(usr))

    users_to_import = list([])
    for usr in yt_users :
        users_to_import.append(usr)
        if len(users_to_import) >= 100:
            target.importUsers(users_to_import)
            users_to_import = list([])
    print target.importUsers(users_to_import)

    print "Importing users finished"

    print "Importing subsystems"
    #getting subsystem names
    subsystem_field_name = get_field_name("subsystem")
    subsystems = client.get_distinct(subsystem_field_name)
    #importing subsystems to yt
    for s in subsystems :
        print "Processing subsystem [ %s ]" % s
        target.createSubsystem(project_id, to_yt_subsystem(s))
    print "Importing subsystems finished"
#
#    for s in subsystems :
#        if (s == "") :
#            continue
#        for subSys in s.split("/") :
#            to_process.add(subSys.strip())
#
#    for s in to_process :
#        print "Processing subsystem [ %s ]" % (s)
#        target.createSubsystem(project_id, to_yt_subsystem(s))
#    print "Importing subsystems finished"

    print "Importing versions"
    #getting version names
    version_field_name = get_field_name("affectsVersion")
    versions = client.get_distinct(version_field_name)
    version_field_name = get_field_name("fixedVersion")
    versions = versions | client.get_distinct(version_field_name)

    for vers in versions :
        if vers == "":
            continue
        print "Processing version [ %s ]" % vers
        target.createVersion(project_id, to_yt_version(vers))
#
#    to_process = set([])
#    for vers in versions :
#        if (vers == "") :
#            continue
#        for v in vers.split("/") :
#            to_process.add(v.strip())
#
#    for vers in to_process :
#        print "Processing version [ %s ]" % (vers)
#        target.createVersion(project_id, to_yt_version(vers))

    print "Importing versions finished"

    print "Creating project custom fields"

#    existing_custom_fields = target.getCustomFields()
#    issue_types = client.get_distinct(get_field_name("type"))
#    contains_type = False
#    bundle_name = "DefaultTypes_enum_" + str(project_name)
#    for cf in existing_custom_fields:
#        if (cf.name == "Type"):
#            # !!! IF YOU DON"T USE "DefaultTypes" FOR TYPE FIELD
#            # YOU SHOULD  DECLARE IT IN THE LINE BELOW
#            # INSTEAD OF "DefaultTypes"
#            bundle_name = "DefaultTypes"
#            contains_type = True
#    if not contains_type:
#        target.createEnumBundleDetailed(bundle_name, [])
#        types_enum = target.getEnumBundle(bundle_name)
#        target.createCustomFieldDetailed("Type", "enum[1]", False, True)
#        target.createProjectCustomFieldDetailed(project_id, "Type", "No type", {"bundle" : bundle_name})
#    else:
#        types_enum = target.getEnumBundle(bundle_name)
#    for t in issue_types:
#        value = get_value("type", t)
#        if not (value in types_enum.values) :
#            target.addValueToEnumBundle(types_enum.name, value)


    #getting custom field names
    header = client.get_header()
    cf_names = set([])
    for elem in header :
        if elem in csvClient.IGNORE_COLUMNS:
            # we don't import data from this column
            continue
        # finding out which fields this element corresponds
        fields = get_keys(elem)
        if not len(fields):
            fields.add(elem)
        for f in fields :
            if not (f in YT_ISSUE_FIELDS) :
            # this field is not default YT field so we will create CF for it
                cf_names.add(f)
    #creating custom fields
    for cf in cf_names :
        print "Processing custom field [ %s ]" % cf
        type_name = "string"
        bundle_name = None
        if cf in csvClient.CUSTOM_FIELD_TYPES:
            type_name = csvClient.CUSTOM_FIELD_TYPES[cf]
            if (type_name == "enum[1]") or (type_name == "enum[*]"):
                # creating enum bundle for the CF
                # we assume that we need to include all  values from that column
                # except those which are in IGNORE_VALUES
                enum_values = client.get_distinct(get_field_name(cf))
                if cf in csvClient.IGNORE_VALUES:
                    ignored_value = csvClient.IGNORE_VALUES[cf]
                    if ignored_value in enum_values:
                        enum_values.remove(ignored_value)
                yt_enum_values = set([])
                for value in enum_values :
                    yt_enum_values.add(get_value(cf, value))
                bundle_name = cf + "_enum_" + str(project_name)
                target.createEnumBundleDetailed(bundle_name, yt_enum_values)
            else :
                # if we don't know the exact type we assume that it is string
                type_name = "string"
        try :
            target.createCustomFieldDetailed(cf, type_name, False, True)
        except BaseException, e:
            print "Prototype for custom field %s already exist" % cf
        target.createProjectCustomFieldDetailed(project_id, cf, "No " + cf, params={'bundle': bundle_name})
    print "Creating project custom fields finished"

    print "Importing issues"
    issues = client.get_issue_list()
    max_count = 100
    id = 1
    yt_issues = list([])
    for elem in issues :
        if csvClient.GENERATE_ID_FOR_ISSUES :
            # if we generate out own numbers IDs for issues
            elem[get_field_name("numberInProject")] = str(id)
            id += 1
        yt_issues.append(to_yt_issue(elem))
        if len(yt_issues) >= max_count:
            print target.importIssues(project_id, project_name + "_assignees", yt_issues)
            yt_issues = list([])
    print target.importIssues(project_id, project_name + "_assignees", yt_issues)
    print "Importing issues finished"

    print "Importing tags"
    tags_field_name = get_field_name("tags")
    for elem in issues :
        id = elem[get_field_name("numberInProject")]
        print "Importing tags for issue [ %s ]" % id
        if not (tags_field_name in elem) :
            continue
        tags = elem[tags_field_name].split(",")
        for t in tags :
            t = t.strip()
            if tags_field_name in csvClient.IGNORE_VALUES:
                if t in csvClient.IGNORE_VALUES[tags_field_name]:
                    continue                
            if t != "":
                print "Processing tag [ %s ]" % t
                target.executeCommand(str(project_id) + "-" + id, "tag " + t)
    print "Importing tags finished"




if __name__ == "__main__":
    main()