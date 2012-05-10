from sync.issues import AsymmetricIssueMerger
from sync.links import IssueBinder, LinkSynchronizer2
from sync.logging import Logger
from sync.executing import SafeCommandExecutor
from youtrack import YouTrackException
from youtrack.connection import Connection
from youtrack2youtrack import youtrack2youtrack
from datetime import datetime
from datetime import timedelta
import csv

batch = 100
sync_map_name = 'sync_map'
slave_to_master_map = {}
config_name = 'sync_config'
config_time_format = '%Y-%m-%d %H:%M:%S:%f'
query_time_format = '%m-%dT%H:%M:%S'
master_sync_field_name = 'Sync with'
empty_field_text = 'No sync with'
last_run = datetime(2012, 1, 1) #default value

project_id = "JT"
tag = "sync"
fields_to_sync = ['state', 'type', 'priority', 'subsystem', 'assignee', 'fix versions', 'affected versions']
#field_name_mapping = {'assignee':'assigneeName', 'fix versions':'fixVersions', 'affected versions':'affectedVersions'}
query = "tag: " + tag

master_url = "http://unit-1"
master_root_login = "root"
master_root_password = "root"
slave_url = "http://unit-2"
slave_root_login = "root"
slave_root_password = "root"

csv.register_dialect('mapper', delimiter=':', quoting=csv.QUOTE_NONE)

def read_sync_map():
    try:
        with open(sync_map_name, 'r') as sync_map_file:
            reader = csv.reader(sync_map_file, 'mapper')
            result = {}
            for row in reader:
              result[row[0]] = row[1]
            return result
    except StopIteration:
        return {}
    except IOError:
        with open(sync_map_name, 'w') as sync_map_file:
            sync_map_file.write('')
        return {}

def write_sync_map(ids_map):
    with open(sync_map_name, 'w') as sync_map_file:
        writer = csv.writer(sync_map_file, 'mapper')
        for key in ids_map.keys():
            writer.writerow([key, ids_map[key]])

def read_last_run():
    try:
        with open(config_name, 'r') as config_file:
            try:
                return datetime.strptime(config_file.readline(), config_time_format)
            except ValueError:
                return datetime(2012, 1, 1)
    except IOError:
        with open(config_name, 'w') as config_file:
            config_file.write('')
        return datetime(2012, 1, 1)

def create_and_attach_sync_field(yt, sync_project_id, sync_field_name):
    sync_field_created = any(field.name == sync_field_name for field in yt.getCustomFields())
    if not sync_field_created:
        yt.createCustomFieldDetailed(sync_field_name, "integer", False, True)
    sync_field_attached = any(field.name == sync_field_name for field in yt.getProjectCustomFields(sync_project_id))
    if not sync_field_attached:
        yt.createProjectCustomFieldDetailed(project_id, sync_field_name, empty_field_text)


def import_to_master(slave_issue):
    master_issue_id = issue_synchronizer.clone_issue_to_master(slave_issue)
    if master_issue_id:
        master_executor.executeCommand(master_issue_id, "tag " + tag)
        slave_executor.executeCommand(slave, slave_issue.id, master_sync_field_name + " " + master_issue_id.rpartition('-')[2])

def import_to_slave(master_issue):
    slave_issue_id = issue_synchronizer.clone_issue_to_slave(master_issue)
    if slave_issue_id:
        slave_executor.executeCommand(slave_issue_id, master_sync_field_name + " " + master_issue.numberInProject)
        slave_executor.executeCommand(slave_issue_id, "tag " + tag)

def sync_to_master(slave_issue):
    issue_synchronizer.sync(None, slave_issue.id)

def sync_to_slave(master_issue):
    issue_synchronizer.sync(master_issue.id, None)

def apply_to_issues(issues_getter, action, excluded_ids=None, log_header=''):
    if not issues_getter or not action: return
    start = 0
    print log_header + ' started...'
    issues = issues_getter(start, batch)
    processed_issue_ids_set = set([])
    while len(issues):
        for issue in issues:
            sync_id = str(issue.id)
            if not (excluded_ids and sync_id in excluded_ids):
                action(issue)
                processed_issue_ids_set.add(sync_id)
        print log_header + ' processed ' + str(start + len(issues)) + ' issues'
        start += batch
        issues = issues_getter(start, batch)
    print log_header + ' action applied to ' + str(len(processed_issue_ids_set)) + ' issues'
    return processed_issue_ids_set

def get_tagged_only_in_slave(start, batch):
    rq = query + ' ' + master_sync_field_name + ':  {' + empty_field_text + '}'
    return slave.getIssues(project_id, rq, start, batch)

def get_tagged_in_master(start, batch):
    rq = query
    return master.getIssues(project_id, rq, start, batch)

def get_formatted_for_query(_datetime):
    return _datetime.strftime(query_time_format)

def get_updated_in_slave_from_last_run(start, batch):
    rq = query + ' updated: ' + get_formatted_for_query(last_run) + " .. " + get_formatted_for_query(current_run)
    return slave.getIssues(project_id, rq, start, batch)

def get_updated_in_master_from_last_run(start, batch):
    rq = query + ' updated: ' + get_formatted_for_query(last_run) + " .. " + get_formatted_for_query(current_run)
    return master.getIssues(project_id, rq, start, batch)

def get_project(slave, project_id):
    try:
        return slave.getProject(project_id)
    except YouTrackException:
        return None

def slave_ids_set_to_sync_ids_set(ids):
    return set([issue_binder.slaveIssueIdToMasterIssueId(id) for id in ids])

def import_project(slave, project_id):
    youtrack2youtrack(master_url, master_root_login, master_root_password, slave_url, slave_root_login, slave_root_password, [project_id], query)
    create_and_attach_sync_field(slave, project_id, master_sync_field_name)
    start = 0
    issues = slave.getIssues(project_id, '', start, batch)
    while len(issues):
        for issue in issues:
            slave_executor.executeCommand(issue.id, master_sync_field_name + " " + issue.numberInProject)
            slave_executor.executeCommand(issue.id, "tag " + tag)
            issue_binder.addBinding(str(issue.id), str(issue.id))
        start += batch
        issues = slave.getIssues(project_id, '', start, batch)

last_run = read_last_run()
current_run = datetime.now()
master = Connection(master_url, master_root_login, master_root_password)
slave = Connection(slave_url, slave_root_login, slave_root_password)
logger = Logger(master, slave, master_root_login, slave_root_login)
master_executor = SafeCommandExecutor(master, logger)
slave_executor = SafeCommandExecutor(slave, logger)
issue_binder = IssueBinder(read_sync_map())
link_synchronizer = LinkSynchronizer2(master_executor, slave_executor, issue_binder)
issue_synchronizer = AsymmetricIssueMerger(master, slave, master_executor, slave_executor, issue_binder, link_synchronizer, fields_to_sync, last_run, current_run, project_id)

DEBUG_MODE = False
master_executor.setDebugMode(DEBUG_MODE)
slave_executor.setDebugMode(DEBUG_MODE)

try:
    if get_project(slave, project_id):
        create_and_attach_sync_field(slave, project_id, master_sync_field_name)

        #1. synchronize sync-issues in slave which have no synchronized clone in master
        imported_slave_ids_set = apply_to_issues(get_tagged_only_in_slave,
            import_to_master,
            log_header='[Sync, Importing new issues from slave to master]')

        #2. synchronize sync-issues in master which have no synchronized clone in slave
        sync_set = set(issue_binder.s_to_m.values())
        imported_master_ids_set = apply_to_issues(get_tagged_in_master,
            import_to_slave,
            excluded_ids=sync_set,
            log_header='[Sync, Importing new issues from master to slave]')

        #3. synchronize sync-issues updated in slave which have synchronized clone in master
        updated_slave_ids_set = apply_to_issues(get_updated_in_slave_from_last_run,
            sync_to_master,
            excluded_ids=imported_slave_ids_set,
            log_header='[Sync, Merging sync issues updated in slave]')

        #4. synchronize sync-issues updated in master which have synchronized clone in slave (if clone hasn't been updated)
        updated_master_ids_set = slave_ids_set_to_sync_ids_set(updated_slave_ids_set) | imported_master_ids_set
        apply_to_issues(get_updated_in_master_from_last_run,
            sync_to_slave,
            excluded_ids=updated_master_ids_set,
            log_header='[Sync, Merging sync issues updated in master and unchanged in slave]')

        #5. synchronize links
        link_synchronizer.syncCollectedLinks()

    else:
        import_project(slave, project_id)

    #write time of script evaluation finish as last run time
    with open(config_name, 'w') as config_file:
        #query time format has 1 second accuracy, so set last run value
        #as current time shifted by the 1 second forward to avoid
        #applying of changes done by the previous script launch
        last_run = datetime.now() + timedelta(seconds=1)
        config_file.write(last_run.strftime(config_time_format))

except Exception, e:
    logger.logError(e, 'Unknown', None, 'failed')
finally:
    logger.finalize()

    #write dictionary of synchronized issues
    write_sync_map(issue_binder.s_to_m)