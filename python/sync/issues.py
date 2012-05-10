import time
from sync.comments import CommentSynchronizer
from sync.fields import AsymmetricFieldsSynchronizer

class AsymmetricIssueMerger(object):
    def __init__(self, master, slave, master_executor, slave_executor, issue_binder, link_synchronizer, fields_to_sync, last_run, current_run, project_id):
        self.master = master
        self.slave = slave
        self.master_executor = master_executor
        self.slave_executor = slave_executor
        self.last_run = last_run
        self.current_run = current_run
        self.comment_sync = CommentSynchronizer(master, slave, master_executor, slave_executor)
        self.field_sync = AsymmetricFieldsSynchronizer(master, slave, master_executor, slave_executor, fields_to_sync)
        self.issue_binder = issue_binder
        self.link_synchronizer = link_synchronizer
        self.project_id = project_id

    def sync(self, master_issue_id, slave_issue_id):
        _master_issue_id = master_issue_id
        _slave_issue_id =  slave_issue_id
        _result = None
        try:
            if not master_issue_id and slave_issue_id:
                _master_issue_id = self.issue_binder.slaveIssueIdToMasterIssueId(slave_issue_id)
                _result = _master_issue_id
            elif not slave_issue_id and master_issue_id:
                _slave_issue_id = self.issue_binder.masterIssueIdToSlaveIssueId(master_issue_id)
                _result = _slave_issue_id
            self._sync(_master_issue_id, _slave_issue_id, self.last_run, self.current_run)
        except KeyError, error:
            print error
        return _result

    def _sync(self, master_issue_id, slave_issue_id, last_run, current_run):
        self.field_sync.syncFields(master_issue_id, slave_issue_id, last_run, current_run)
        self.comment_sync.syncComments(master_issue_id, slave_issue_id)
        self.link_synchronizer.collectLinksToSyncById(master_issue_id, slave_issue_id)

    def clone_issue_to_master(self, issue_from):
        safe_summary = issue_from.summary if hasattr(issue_from, 'summary') else ''
        safe_description = issue_from.description if hasattr(issue_from, 'description') else ''
        created_issue_id = self.master_executor.createIssue(self.project_id, safe_summary, safe_description, issue_from.id)
        if created_issue_id: self._sync(created_issue_id, issue_from.id, None, self.current_run)
        return created_issue_id

    def clone_issue_to_slave(self, issue_from):
        safe_summary = issue_from.summary if hasattr(issue_from, 'summary') else ''
        safe_description = issue_from.description if hasattr(issue_from, 'description') else ''
        created_issue_id = self.slave_executor.createIssue(self.project_id, safe_summary, safe_description, issue_from.id)
        if created_issue_id: self._sync(issue_from.id, created_issue_id, None, self.current_run)
        return created_issue_id