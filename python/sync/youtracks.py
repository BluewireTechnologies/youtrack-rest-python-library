from sync.executing import SafeCommandExecutor
from sync.issues import AsymmetricIssueMerger
from sync.links import LinkSynchronizer

query_time_format = '%m-%dT%H:%M:%S'
batch = 100
tag = "sync"
master_sync_field_name = 'Sync with'
empty_field_text = 'No sync with'

def get_formatted_for_query(_datetime):
    return _datetime.strftime(query_time_format)

def get_advanced_query(query, _last_run, _current_run):
    return query + ' updated: ' + get_formatted_for_query(_last_run) + " .. " + get_formatted_for_query(_current_run)

class YouTrackSynchronizer(object):
    def __init__(self, master, slave, logger, issue_binder, project_id, fields_to_sync, query, last_run=None, current_run=None):
        self.slave = None
        self.master = master
        self.slave = slave
        self.logger = logger
        self.master_executor = SafeCommandExecutor(master, logger)
        self.slave_executor = SafeCommandExecutor(slave, logger)
        self.issue_binder = issue_binder
        self.query = query
        self.last_run = last_run
        self.current_run = current_run
        self.project_id = project_id
        self.link_synchronizer = LinkSynchronizer(self.master_executor, self.slave_executor, self.issue_binder)
        self.issue_synchronizer = AsymmetricIssueMerger(master, slave, self.master_executor, self.slave_executor, self.issue_binder, self.link_synchronizer, fields_to_sync, last_run, current_run, project_id)

    def setDebugMode(self, on):
        self.master_executor.setDebugMode(on)
        self.slave_executor.setDebugMode(on)

    def sync(self):
        #0. create if not existed and attach synchronization field
        self._create_and_attach_sync_field(self.slave, self.project_id, master_sync_field_name)

        #1. synchronize sync-issues in slave which have no synchronized clone in master
        imported_slave_ids_set = self._apply_to_issues(self._get_tagged_only_in_slave,
            self._import_to_master,
            log_header='[Sync, Importing new issues from slave to master]')

        #2. synchronize sync-issues in master which have no synchronized clone in slave
        sync_set = set(self.issue_binder.s_to_m.values())
        imported_master_ids_set = self._apply_to_issues(self._get_tagged_in_master,
            self._import_to_slave,
            excluded_ids=sync_set,
            log_header='[Sync, Importing new issues from master to slave]')

        #3. synchronize sync-issues updated in slave which have synchronized clone in master
        updated_slave_ids_set = self._apply_to_issues(self._get_updated_in_slave_from_last_run,
            self._sync_to_master,
            excluded_ids=imported_slave_ids_set,
            log_header='[Sync, Merging sync issues updated in slave]')

        #4. synchronize sync-issues updated in master which have synchronized clone in slave (if clone hasn't been updated)
        updated_master_ids_set = self._slave_ids_set_to_sync_ids_set(updated_slave_ids_set) | imported_master_ids_set
        self._apply_to_issues(self._get_updated_in_master_from_last_run,
            self._sync_to_slave,
            excluded_ids=updated_master_ids_set,
            log_header='[Sync, Merging sync issues updated in master and unchanged in slave]')

        #5. synchronize links
        self.link_synchronizer.syncCollectedLinks()

    def syncAfterImport(self):
        self._create_and_attach_sync_field(self.slave, self.project_id, master_sync_field_name)
        start = 0
        issues = self.slave.getIssues(self.project_id, '', start, batch)
        while len(issues):
            for issue in issues:
                issue_id = issue.id
                issue_number = issue_id.rpartition('-')[2]
                self._mark_issues_as_sync(issue_number, issue_id, issue_id)
            start += batch
            issues = self.slave.getIssues(self.project_id, '', start, batch)

    def _slave_ids_set_to_sync_ids_set(self, ids):
        return set([self.issue_binder.slaveIssueIdToMasterIssueId(id) for id in ids])

    def _import_to_master(self, slave_issue):
        master_issue_id = self.issue_synchronizer.clone_issue_to_master(slave_issue)
        if master_issue_id:
            self._mark_issues_as_sync(master_issue_id.rpartition('-')[2], master_issue_id, slave_issue.id)

    def _import_to_slave(self, master_issue):
        slave_issue_id = self.issue_synchronizer.clone_issue_to_slave(master_issue)
        if slave_issue_id:
            self._mark_issues_as_sync(master_issue.numberInProject, master_issue.id, slave_issue_id)

    def _sync_to_master(self, slave_issue):
        self.issue_synchronizer.sync(None, slave_issue.id)

    def _sync_to_slave(self, master_issue):
        self.issue_synchronizer.sync(master_issue.id, None)

    def _apply_to_issues(self, issues_getter, action, excluded_ids=None, log_header=''):
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

    def _get_tagged_only_in_slave(self, start, batch):
        rq = self.query + ' ' + master_sync_field_name + ':  {' + empty_field_text + '}'
        return self.slave.getIssues(self.project_id, rq, start, batch)

    def _get_tagged_in_master(self, start, batch):
        rq = self.query
        return self.master.getIssues(self.project_id, rq, start, batch)

    def _get_updated_in_slave_from_last_run(self, start, batch):
        rq = get_advanced_query(self.query, self.last_run, self.current_run)
        return self.slave.getIssues(self.project_id, rq, start, batch)

    def _get_updated_in_master_from_last_run(self, start, batch):
        rq = get_advanced_query(self.query, self.last_run, self.current_run)
        return self.master.getIssues(self.project_id, rq, start, batch)

    def _mark_issues_as_sync(self, master_issue_number, master_issue_id, slave_issue_id):
        self.master_executor.executeCommand(master_issue_id, "tag " + tag)
        self.slave_executor.executeCommand(slave_issue_id, "tag " + tag)
        self.slave_executor.executeCommand(slave_issue_id, master_sync_field_name + " " + master_issue_number)
        self.issue_binder.addBinding(master_issue_id, slave_issue_id)

    def _create_and_attach_sync_field(self, yt, project_id, sync_field_name):
        sync_field_created = any(field.name == sync_field_name for field in yt.getCustomFields())
        if not sync_field_created:
            yt.createCustomFieldDetailed(sync_field_name, "integer", False, True)
        sync_field_attached = any(field.name == sync_field_name for field in yt.getProjectCustomFields(project_id))
        if not sync_field_attached:
            yt.createProjectCustomFieldDetailed(project_id, sync_field_name, empty_field_text)
