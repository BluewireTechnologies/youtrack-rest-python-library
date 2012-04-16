from youtrack import YouTrackException
from youtrack.connection import Connection
from youtrack2youtrack import youtrack2youtrack
from datetime import datetime
import time

project_id = "JT"
tag = "sync"
fields_to_sync = ['state', 'type', 'priority', 'subsystem', 'assigneeName', 'fixVersions', 'affectedVersions']
priority_mapping= {'0':'Show-stopper', '1':'Critical', '2':'Major', '3':'Normal', '4':'Minor'}
query = "tag: " + tag
master_url = "http://unit-276:8888"
slave_url = "http://unit-276:8088"
batch = 100
config_name = 'sync_config'
config_time_format = '%Y-%m-%d %H:%M:%S:%f'
query_time_format = '%m-%dT%H:%M:%S'
links_to_be_added_in_slave = []
links_to_be_added_in_master = []

last_run = datetime(2012, 1, 1)
current_run = datetime.now()
try:
    with open(config_name, 'r') as config_file:
        try:
            last_run = datetime.strptime(config_file.readline(), config_time_format)
        except ValueError:
            last_run = datetime(2012, 1, 1)
except IOError:
    with open(config_name, 'w') as config_file:
        config_file.write('')

def get_formatted_for_query(_datetime):
    return _datetime.strftime(query_time_format)

def get_in_milliseconds(_datetime):
    return int(round(1e+3*time.mktime(_datetime.timetuple()) + 1e-3*_datetime.microsecond))

def get_updated_issues(yt, start, updated_after, updated_before):
    refined_query = query + " updated: " + get_formatted_for_query(updated_after) + " .. " + get_formatted_for_query(updated_before)
    return yt.getIssues(project_id, refined_query, start, batch)

def get_issue_changes(yt, issue, after, before):
#    yt.headers['Accepts'] = 'application/json;charset=utf-8'
    result = yt.get_changes_for_issue(issue.id)
    after_ms = get_in_milliseconds(after)
    before_ms = get_in_milliseconds(before)
    new_changes = []
    for change in result:
        change_time = change['updated']
        if (change_time > after_ms) & (change_time < before_ms):
            new_changes.append(change)
    return new_changes

def apply_changes_to_issue(to_yt, from_yt, issue_id, changes, fields_to_ignore = []):
    changed_fields = set()
    for change in changes:
        run_as = change.updater_name
        to_yt.importUsers([from_yt.getUser(run_as)])
        comment = None
        if len(change.comments):
            comment = change.comments[0]
        command = ""
        for field in change.fields:
            field_name = field.name.lower()
            if field.name != 'links' and field_name in fields_to_sync and field_name not in fields_to_ignore:
                for field_value in field.new_value:
                    changed_fields.add(field_name)
                    command += get_command_set_value_to_field(field_name, field_value)
        if (not len(command)) and comment is not None:
            command = comment
        to_yt.executeCommand(issue_id, command, comment, run_as=run_as)
        #print "Executing command: " + command + " for issue " + issue_id + " in " + to_yt
    return changed_fields

def get_command_set_value_to_field(field, field_value):
    command = ""
    if len(field_value):
        if isinstance(field_value, list):
            for value in field_value:
                command += field + " " + value + " "
        else:
            if field == 'priority':
                if field_value in priority_mapping.keys():
                    field_value = priority_mapping[field_value]
            if field == 'assigneeName':
                field = 'Assignee'
            command += field + " " + field_value + " "
    return command

def apply_changes_to_new_issue(yt, issue_id_to_apply, original_issue):
    command = ""
    for field in fields_to_sync:
        if hasattr(original_issue, field):
            field_value = original_issue[field]
            command += get_command_set_value_to_field(field, field_value)

    yt.executeCommand(issue_id_to_apply, command)
    for comment in original_issue.getComments():
        yt.executeCommand(issue_id_to_apply, "comment", comment.text, None, comment.author)

def merge_and_apply_changes(left_yt, left_issue_id, left_changes, right_yt, right_issue_id, right_changes):
    changed_fields = apply_changes_to_issue(right_yt, left_yt, right_issue_id, left_changes)
    apply_changes_to_issue(left_yt, right_yt, left_issue_id, right_changes, changed_fields)

def create_and_attach_sync_field(yt, sync_project_id, sync_field_name):
    sync_field_created = any(field.name == sync_field_name for field in yt.getCustomFields())
    if not sync_field_created:
        yt.createCustomFieldDetailed(sync_field_name, "integer", False, True, True)
    sync_field_attached = any(field.name == sync_field_name for field in yt.getProjectCustomFields(sync_project_id))
    if not sync_field_attached:
        yt.createProjectCustomFieldDetailed(project_id, sync_field_name, 'No sync')

def import_sync_issues_to_slave():
    youtrack2youtrack(master_url, "root", "root", slave_url, "root", "root", [project_id], query)
    create_and_attach_sync_field(slave, project_id, master_sync_field_name)
    go_on = True
    start = 0
    while go_on:
        go_on = False
        issues = slave.getIssues(project_id, '', start, batch)
        start += batch
        for issue in issues:
            go_on = True
            slave.executeCommand(issue.id, master_sync_field_name + " " + issue.numberInProject)

def merge_links(slave_links, master_links):
    if len(master_links):
        global links_to_be_added_in_slave
        links_to_be_added_in_slave += [link for link in master_links if link not in slave_links]
    if len(slave_links):
        global links_to_be_added_in_master
        links_to_be_added_in_slave += [link for link in slave_links if link not in master_links]

def sync_to_master(slave_issue):
    assert slave_issue[master_sync_field_name] is not None
    master_issue = master.getIssue(project_id + '-' + slave_issue[master_sync_field_name])
    slave_changes = get_issue_changes(slave, slave_issue, last_run, current_run)
    master_changes = get_issue_changes(master, master_issue, last_run, current_run)
    changed_fields = apply_changes_to_issue(slave, master, slave_issue.id, master_changes)
    apply_changes_to_issue(master, slave, master_issue.id, slave_changes, changed_fields)
    merge_links(slave_issue.getLinks(True), master_issue.getLinks(True))

def sync_to_slave(master_issue):
    slave_issues = slave.getIssues(project_id, master_sync_field_name + ": " + master_issue.numberInProject, 0, 1)
    if len(slave_issues):
        slave_issue = slave_issues[0]
        master_changes = get_issue_changes(master, master_issue, last_run, current_run)
        apply_changes_to_issue(slave, master, slave_issue.id, master_changes)
        merge_links(slave_issue.getLinks(True), master_issue.getLinks(True))
    else:
        created_issue_number = slave.createIssue(project_id, None, master_issue.summary, master_issue.description, None, None, None, None, None, None, None).rpartition('-')[2]
        slave_issue_id = project_id + "-" + created_issue_number
        apply_changes_to_new_issue(slave, slave_issue_id, master_issue)
        slave.executeCommand(slave_issue_id, master_sync_field_name + " " + issue.numberInProject)
        slave.executeCommand(slave_issue_id, "tag " + tag)
        merge_links([], master_issue.getLinks(True))

master_sync_field_name = 'masterIssueId'

master = Connection(master_url, "root", "root")
slave = Connection(slave_url, "root", "root")

try:
    slave.getProject(project_id)
    create_and_attach_sync_field(slave, project_id, master_sync_field_name)
except YouTrackException:
    import_sync_issues_to_slave()

#synchronize sync-issues updated in slave
start = 0
updated_sync_slave_issues = get_updated_issues(slave, start, last_run, current_run)
uploaded = len(updated_sync_slave_issues)
processed_sync_master_issues = []
while uploaded:
    for slave_issue in updated_sync_slave_issues:
        sync_to_master(slave_issue)
        processed_sync_master_issues.append(master.getIssue(project_id + '-' + slave_issue[master_sync_field_name]))
    start += uploaded
    updated_sync_slave_issues = get_updated_issues(slave, start, last_run, current_run)
    uploaded = len(updated_sync_slave_issues)

#synchronize sync-issues updated only in master
start = 0
updated_sync_master_issues = get_updated_issues(master, start, last_run, current_run)
uploaded = len(updated_sync_master_issues)
while uploaded:
    updated_only_in_master = [issue for issue in updated_sync_master_issues if issue not in processed_sync_master_issues]
    for master_issue in updated_only_in_master:
        sync_to_slave(master_issue)
    start += uploaded
    updated_sync_master_issues = get_updated_issues(master, start, last_run, current_run)
    uploaded = len(updated_sync_master_issues)

for link in links_to_be_added_in_slave:
#    source = link.source
#    link.source = link.target
#    link.target = source
    link.source = slave.getIssues(project_id, master_sync_field_name + ": " + link.source.rpartition('-')[2], 0, 1)[0].id
    link.target = slave.getIssues(project_id, master_sync_field_name + ": " + link.traget.rpartition('-')[2], 0, 1)[0].id

for link in links_to_be_added_in_master:
#    source = link.source
#    link.source = link.target
#    link.target = source
    link.source = project_id + "-" + slave.getIssue(link.source)[master_sync_field_name]
    link.target = project_id + "-" + slave.getIssue(link.target)[master_sync_field_name]

slave.importLinks(links_to_be_added_in_slave)
master.importLinks(links_to_be_added_in_master)

#write time of script evaluation finish as last run time
with open(config_name, 'w') as config_file:
    config_file.write(datetime.now().strftime(config_time_format))

