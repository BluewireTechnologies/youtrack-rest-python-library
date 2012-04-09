from youtrack import YouTrackException
from youtrack.connection import Connection
from youtrack2youtrack import youtrack2youtrack

last_run = 0
project_id = "JT"
tag = "sync"
fields_to_sync = ['state', 'type', 'priority', 'subsystem', 'assigneeName', 'fixVersions', 'affectedVersions']
query = "tag: " + tag

def get_updated_issues(yt, after):
    return yt.getIssues(project_id, query, 0, 100)

def get_issue_changes(yt, issue, after):
#    yt.headers['Accepts'] = 'application/json;charset=utf-8'
    result = yt.get_changes_for_issue(issue.id)
    new_changes = []
    for change in result:
        if change['updated'] < after:
            break
        else:
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
                for value in field.new_value:
                    changed_fields.add(field_name)
                    command += field_name + " " + value + " "
        if (not len(command)) and comment is not None:
            command = comment
        to_yt.executeCommand(project_id + "-" + issue_id, command, comment, run_as=run_as)
    return changed_fields


def apply_changes_to_new_issue(yt, issue_id_to_apply, original_issue):
    command = ""
    for field in fields_to_sync:
        field_value = original_issue[field]
        if len(field_value):
            if isinstance(field_value, list):
                for value in field_value:
                    command += field + " " + value + " "
            else:
                command += field + " " + field_value + " "

    yt.executeCommand(project_id + "-" + issue_id_to_apply, command)
    for comment in original_issue.getComments():
        yt.executeCommand(issue_id_to_apply, "comment", comment.text, None, comment.author)

def merge_and_apply_changes(left_yt, left_issue_id, left_changes, right_yt, right_issue_id, right_changes):
    changed_fields = apply_changes_to_issue(right_yt, left_yt, right_issue_id, left_changes)
    apply_changes_to_issue(left_yt, right_yt, left_issue_id, right_changes, changed_fields)

master_issue_id_field_name = 'masterIssueId'

master = Connection("http://teamsys.labs.intellij.net", "root", "root")
slave = Connection("http://localhost:13864", "root", "root")

try:
    slave.getProject(project_id)
except YouTrackException:
    slave.createCustomFieldDetailed(master, "integer", False, True, True)
    youtrack2youtrack("http://teamsys.labs.intellij.net", "root", "root", "http://localhost:13864", "root", "root", [project_id], query)
    go_on = True
    start = 0
    amount = 100
    while go_on:
        go_on = False
        issues = slave.getIssues(project_id, '', start, amount)
        start += amount
        for issue in issues:
            go_on = True
            slave.executeCommand(issue.id, master_issue_id_field_name + " " + issue.numberInProject)


updated_master_issues = get_updated_issues(master, last_run)
updated_slave_issues = get_updated_issues(slave, last_run)

updated_slave_issue_ids = [issue[master_issue_id_field_name] for issue in updated_slave_issues if
                           master_issue_id_field_name in issue and issue[master_issue_id_field_name] is not None]
updated_master_issue_ids = [issue.numberInProject for issue in updated_master_issues]

changed_in_master = [issue for issue in updated_master_issues if issue.numberInProject not in updated_slave_issue_ids]
changed_in_slave = [issue for issue in updated_slave_issues if
                    master_issue_id_field_name not in issue or issue[
                                                               master_issue_id_field_name] not in updated_slave_issue_ids]
changed_in_both = [issue for issue in updated_slave_issue_ids if
                   master_issue_id_field_name in issue and issue[master_issue_id_field_name] in updated_master_issue_ids]

links_to_be_added_in_slave = []
links_to_be_removed_in_slave = []
links_to_be_added_in_master = []
links_to_be_removed_in_master = []

for issue in changed_in_slave:
    links_to_be_added_in_master += issue.getLinks(True)
    if master_issue_id_field_name in issue:
        master_issue_id = issue[master_issue_id_field_name]
        if master_issue_id is not None:
            changes = get_issue_changes(slave, issue, last_run)
            apply_changes_to_issue(master, slave, master_issue_id, changes)
            continue
        #if we are here now, it means that issue is not currently in master instance, so create it!
    created_issue = master.createIssue(project_id, None, issue.summary, issue.description, None, None, None, None, None,
        None, None)
    issue_id = created_issue.rpartition('-')[2]
    apply_changes_to_new_issue(master, issue_id, issue)
    master.executeCommand(issue_id, "tag " + tag)
    slave.executeCommand(issue.id, master_issue_id_field_name + " " + issue_id)

for issue in changed_in_master:
    links_to_be_added_in_slave += issue.getLinks(True)
    slave_issues = slave.getIssues(project_id, master_issue_id_field_name + ": " + issue.id, 0, 1)
    if len(slave_issues):
        slave_issue_id = slave_issues[0].id
        changes = get_issue_changes(master, issue, last_run)
        apply_changes_to_issue(slave, master, slave_issue_id, changes)
    else:
        slave_issue_id = project_id + "-" + slave.createIssue(project_id, issue.summary, issue.description, None, None, None, None, None,
            None, None, None).rpartition('-')[2]
        apply_changes_to_new_issue(slave, slave_issue_id, issue)
        slave.executeCommand(slave_issue_id, master_issue_id_field_name + " " + issue.numberInProject)
        slave.executeCommand(slave_issue_id, "tag " + tag)

for issue in changed_in_both:
    links_to_be_added_in_master += issue.getLinks(True)
    slave_changes = get_issue_changes(slave, issue, last_run)
    master_issue_id = project_id + "-" + issue[master_issue_id_field_name]
    links_to_be_added_in_slave += master.getIssue(master_issue_id).getLinks(True)
    master_changes = get_issue_changes(master, master.getIssue(master_issue_id), last_run)
    merge_and_apply_changes(slave, issue.id, slave_changes, master, master_issue_id, master_changes)

for link in links_to_be_added_in_slave:
    source = link.source
#    link.source = link.target
#    link.target = source
    link.source = slave.getIssues(project_id, master_issue_id_field_name + ": " + link.source.rpartition('-')[2], 0, 1)[0].id
    link.target = slave.getIssues(project_id, master_issue_id_field_name + ": " + link.traget.rpartition('-')[2], 0, 1)[0].id

for link in links_to_be_added_in_master:
    source = link.source
#    link.source = link.target
#    link.target = source
    link.source = project_id + "-" + slave.getIssue(link.source)[master_issue_id_field_name]
    link.target = project_id + "-" + slave.getIssue(link.target)[master_issue_id_field_name]

slave.importLinks(links_to_be_added_in_slave)
master.importLinks(links_to_be_added_in_master)


