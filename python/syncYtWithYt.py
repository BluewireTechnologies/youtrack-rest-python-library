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



with open(config_name, 'w') as config_file:
    last_run_str = current_run.strftime(config_time_format)
    config_file.write(last_run_str)


def get_formatted_for_query(_datetime):
    return _datetime.strftime("%m-%dT%H:%M:%S")

def get_in_milliseconds(_datetime):
    return int(round(1e+3*time.mktime(_datetime.timetuple()) + 1e-3*_datetime.microsecond))

def get_updated_issues(yt, after):
    refined_query = query + " updated: " + get_formatted_for_query(last_run) + " .. " + get_formatted_for_query(current_run)
    return yt.getIssues(project_id, refined_query, 0, batch)

def get_issue_changes(yt, issue, after):
#    yt.headers['Accepts'] = 'application/json;charset=utf-8'
    result = yt.get_changes_for_issue(issue.id)
    last_sync_time = get_in_milliseconds(after)
    new_changes = []
    for change in result:
        if change['updated'] > last_sync_time:
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

master_sync_field_name = 'masterIssueId'

master = Connection(master_url, "root", "root")
slave = Connection(slave_url, "root", "root")

try:
    slave.getProject(project_id)
    create_and_attach_sync_field(slave, project_id, master_sync_field_name)
except YouTrackException:
    #import project from master
    youtrack2youtrack(master_url, "root", "root", slave_url, "root", "root", [project_id], query)
    create_and_attach_sync_field(slave, project_id, master_sync_field_name)
    go_on = True
    start = 0
    amount = batch
    while go_on:
        go_on = False
        issues = slave.getIssues(project_id, '', start, amount)
        start += amount
        for issue in issues:
            go_on = True
            slave.executeCommand(issue.id, master_sync_field_name + " " + issue.numberInProject)


updated_master_issues = get_updated_issues(master, last_run)
updated_slave_issues = get_updated_issues(slave, last_run)

updated_slave_issue_ids = [issue[master_sync_field_name] for issue in updated_slave_issues if
                           master_sync_field_name in issue and issue[master_sync_field_name] is not None]
updated_master_issue_ids = [issue.numberInProject for issue in updated_master_issues]

changed_in_master = [issue for issue in updated_master_issues if issue.numberInProject not in updated_slave_issue_ids]
changed_in_slave = [issue for issue in updated_slave_issues if
                    master_sync_field_name not in issue or issue[
                                                               master_sync_field_name] not in updated_slave_issue_ids]
changed_in_both = [issue for issue in updated_slave_issues if
                   master_sync_field_name in issue and issue[master_sync_field_name] in updated_master_issue_ids]

links_to_be_added_in_slave = []
links_to_be_removed_in_slave = []
links_to_be_added_in_master = []
links_to_be_removed_in_master = []

for issue in changed_in_slave:
    links_to_be_added_in_master += issue.getLinks(True)
    if master_sync_field_name in issue:
        master_issue_id = issue[master_sync_field_name]
        if master_issue_id is not None:
            changes = get_issue_changes(slave, issue, last_run)
            apply_changes_to_issue(master, slave, master_issue_id, changes)
            continue
        #if we are here now, it means that issue is not currently in master instance, so create it!
    created_issue_number = master.createIssue(project_id, None, issue.summary, issue.description, None, None, None, None, None, None, None).rpartition('-')[2]
    master_issue_id = project_id + "-" + created_issue_number
    apply_changes_to_new_issue(master, master_issue_id, issue)
    master.executeCommand(master_issue_id, "tag " + tag)
    slave.executeCommand(issue.id, master_sync_field_name + " " + created_issue_number)

for issue in changed_in_master:
    links_to_be_added_in_slave += issue.getLinks(True)
    slave_issues = slave.getIssues(project_id, master_sync_field_name + ": " + issue.numberInProject, 0, 1)
    if len(slave_issues):
        slave_issue_id = slave_issues[0].id
        changes = get_issue_changes(master, issue, last_run)
        apply_changes_to_issue(slave, master, slave_issue_id, changes)
    else:
        created_issue_number = slave.createIssue(project_id, None, issue.summary, issue.description, None, None, None, None, None, None, None).rpartition('-')[2]
        slave_issue_id = project_id + "-" + created_issue_number
        apply_changes_to_new_issue(slave, slave_issue_id, issue)
        slave.executeCommand(slave_issue_id, master_sync_field_name + " " + issue.numberInProject)
        slave.executeCommand(slave_issue_id, "tag " + tag)

for issue in changed_in_both:
    links_to_be_added_in_master += issue.getLinks(True)
    slave_changes = get_issue_changes(slave, issue, last_run)
    master_issue_id = project_id + "-" + issue[master_sync_field_name]
    links_to_be_added_in_slave += master.getIssue(master_issue_id).getLinks(True)
    master_changes = get_issue_changes(master, master.getIssue(master_issue_id), last_run)
    merge_and_apply_changes(slave, issue.id, slave_changes, master, master_issue_id, master_changes)

for link in links_to_be_added_in_slave:
    source = link.source
#    link.source = link.target
#    link.target = source
    link.source = slave.getIssues(project_id, master_sync_field_name + ": " + link.source.rpartition('-')[2], 0, 1)[0].id
    link.target = slave.getIssues(project_id, master_sync_field_name + ": " + link.traget.rpartition('-')[2], 0, 1)[0].id

for link in links_to_be_added_in_master:
    source = link.source
#    link.source = link.target
#    link.target = source
    link.source = project_id + "-" + slave.getIssue(link.source)[master_sync_field_name]
    link.target = project_id + "-" + slave.getIssue(link.target)[master_sync_field_name]

slave.importLinks(links_to_be_added_in_slave)
master.importLinks(links_to_be_added_in_master)


