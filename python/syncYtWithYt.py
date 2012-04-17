from youtrack import YouTrackException
from youtrack.connection import Connection
from youtrack2youtrack import youtrack2youtrack
from datetime import datetime
import time

project_id = "JT"
tag = "sync"
fields_to_sync = ['state', 'type', 'priority', 'subsystem', 'assignee', 'fixVersions', 'affectedVersions']
priority_mapping= {'0':'Show-stopper', '1':'Critical', '2':'Major', '3':'Normal', '4':'Minor'}
query = "tag: " + tag
master_url = "http://unit-276:8888"
master_root_login = "root"
master_root_password = "root"
slave_url = "http://unit-276:8088"
slave_root_login = "root"
slave_root_password = "root"
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
        if (change_time > after_ms) and (change_time < before_ms):
            new_changes.append(change)
    return new_changes

def executeSyncCommand(yt, issue_id, command, comment, run_as):
    if command != '':
        yt.executeCommand(issue_id, command, comment, run_as=run_as)
        yt_name = 'Master' if yt == master else 'Slave'
        user_login = (master_root_login if yt == master else slave_root_login) if run_as is None else run_as
        print '[Sync, ' + issue_id + ', ' + yt_name + '] apply command: \"' + command + '\" as ' + user_login


def apply_changes_to_issue(to_yt, from_yt, issue_id, changes, fields_to_ignore = []):
    changed_fields = set()
    for change in changes:
        run_as = change.updater_name
        to_yt.importUsers([from_yt.getUser(run_as)])
        comment = None
        if len(change.comments):
            comment = change.comments[0]
        command = ''
        for field in change.fields:
            field_name = field.name.lower()
            if field.name != 'links' and field_name in fields_to_sync and field_name not in fields_to_ignore:
                for field_value in field.new_value:
                    changed_fields.add(field_name)
                    command += get_command_set_value_to_field(field_name, field_value)
        if (not len(command)) and comment is not None:
            command = comment
        executeSyncCommand(to_yt, issue_id, command, comment, run_as)
    return changed_fields

def get_command_set_value_to_field(field, field_value):
    command = ""
    if len(field_value):
        if isinstance(field_value, list):
            for value in field_value:
                command += field + " " + value + " "
        else:
            if field == 'priority' and field_value in priority_mapping.keys():
                field_value = priority_mapping[field_value]
            command += field + " " + field_value + " "
    return command

def apply_changes_to_new_issue(yt, issue_id_to_apply, original_issue):
    command = ''
    for field in fields_to_sync:
        internal_field = 'assigneeName' if field == 'assignee' else field
        if hasattr(original_issue, internal_field):
            field_value = original_issue[internal_field]
            command += get_command_set_value_to_field(field, field_value)
    executeSyncCommand(yt, issue_id_to_apply, command, None, None)
    for comment in original_issue.getComments():
        executeSyncCommand(yt, issue_id_to_apply, "comment", comment.text, comment.author)

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

def clone_issue(yt_to, issue_from):
    created_issue_number = yt_to.createIssue(project_id, None, issue_from.summary, issue_from.description, None, None, None, None, None, None, None).rpartition('-')[2]
    created_issue_id = project_id + '-' + created_issue_number
    yt_name = 'Master' if yt_to == master else 'Slave'
    print '[Sync, ' + created_issue_id + ', ' + yt_name + '] created'
    apply_changes_to_new_issue(yt_to, created_issue_id, issue_from)
    return created_issue_id


def import_sync_issues_to_slave():
    youtrack2youtrack(master_url, master_root_login, master_root_password, slave_url, slave_root_login, slave_root_password, [project_id], query)
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
        links_to_be_added_in_master += [link for link in slave_links if link not in master_links]

def sync_to_master(slave_issue):
    if hasattr(slave_issue, master_sync_field_name):
        master_issue = master.getIssue(project_id + '-' + slave_issue[master_sync_field_name])
        slave_changes = get_issue_changes(slave, slave_issue, last_run, current_run)
        master_changes = get_issue_changes(master, master_issue, last_run, current_run)
        changed_fields = apply_changes_to_issue(slave, master, slave_issue.id, master_changes)
        apply_changes_to_issue(master, slave, master_issue.id, slave_changes, changed_fields)
        merge_links(slave_issue.getLinks(True), master_issue.getLinks(True))
        return master_issue.id
    else:
        #issue in slave with no sync issue in master
        master_issue_id = clone_issue(master, slave_issue)
        master.executeCommand(master_issue_id, "tag " + tag)
        slave.executeCommand(slave_issue.id, master_sync_field_name + " " + master_issue_id.rpartition('-')[2])
        merge_links(slave_issue.getLinks(True), [])
        return master_issue_id

def sync_to_slave(master_issue):
    slave_issues = slave.getIssues(project_id, master_sync_field_name + ": " + master_issue.numberInProject, 0, 1)
    if len(slave_issues):
        slave_issue = slave_issues[0]
        master_changes = get_issue_changes(master, master_issue, last_run, current_run)
        apply_changes_to_issue(slave, master, slave_issue.id, master_changes)
        merge_links(slave_issue.getLinks(True), master_issue.getLinks(True))
        return slave_issue.id
    else:
        #issue in master with no sync issue in slave
        slave_issue_id = clone_issue(slave, master_issue)
        slave.executeCommand(slave_issue_id, master_sync_field_name + " " + master_issue.numberInProject)
        slave.executeCommand(slave_issue_id, "tag " + tag)
        merge_links([], master_issue.getLinks(True))
        return slave_issue_id

master_sync_field_name = 'masterIssueId'

master = Connection(master_url, master_root_login, master_root_password)
slave = Connection(slave_url, slave_root_login, slave_root_password)

try:
    slave.getProject(project_id)
    create_and_attach_sync_field(slave, project_id, master_sync_field_name)
except YouTrackException:
    import_sync_issues_to_slave()

#synchronize sync-issues updated in slave
start = 0
updated_sync_slave_issues = get_updated_issues(slave, start, last_run, current_run)
uploaded = len(updated_sync_slave_issues)
processed_sync_master_issue_ids = []
while uploaded:
    for slave_issue in updated_sync_slave_issues:
        processed_sync_master_issue_ids.append(sync_to_master(slave_issue))
    start += uploaded
    updated_sync_slave_issues = get_updated_issues(slave, start, last_run, current_run)
    uploaded = len(updated_sync_slave_issues)

#synchronize sync-issues updated only in master
start = 0
updated_sync_master_issues = get_updated_issues(master, start, last_run, current_run)
uploaded = len(updated_sync_master_issues)
while uploaded:
    updated_only_in_master = [issue for issue in updated_sync_master_issues if issue.id not in processed_sync_master_issue_ids]
    for master_issue in updated_only_in_master:
        sync_to_slave(master_issue)
    start += uploaded
    updated_sync_master_issues = get_updated_issues(master, start, last_run, current_run)
    uploaded = len(updated_sync_master_issues)

#links synchronization
for link in links_to_be_added_in_slave:
    link.source = slave.getIssues(project_id, master_sync_field_name + ": " + link.source.rpartition('-')[2], 0, 1)[0].id
    link.target = slave.getIssues(project_id, master_sync_field_name + ": " + link.traget.rpartition('-')[2], 0, 1)[0].id

for link in links_to_be_added_in_master:
    link.source = project_id + "-" + slave.getIssue(link.source)[master_sync_field_name]
    link.target = project_id + "-" + slave.getIssue(link.target)[master_sync_field_name]

def check_link(yt, link):
    source_issue_tagged = len(yt.getIssues(project_id, 'issue id: ' + link.source + ' ' + query, 0, 1))
    target_issue_tagged = len(yt.getIssues(project_id, 'issue id: ' + link.target + ' ' + query, 0, 1))
    return source_issue_tagged and target_issue_tagged

valid_links_to_be_added_in_slave = [link for link in links_to_be_added_in_slave if check_link(slave, link)]
valid_links_to_be_added_in_master = [link for link in links_to_be_added_in_master if check_link(master, link)]

slave.importLinks(valid_links_to_be_added_in_slave)
master.importLinks(valid_links_to_be_added_in_master)

#write time of script evaluation finish as last run time
with open(config_name, 'w') as config_file:
    config_file.write(datetime.now().strftime(config_time_format))

