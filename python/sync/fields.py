import time
import sys
from sync.states import get_command_for_state_change, get_event
from youtrack import YouTrackException

PRIORITY_MAPPING= {'0':'Show-stopper', '1':'Critical', '2':'Major', '3':'Normal', '4':'Minor'}

def get_issue_changes(yt, issue_id, start=None, finish=None):
     result = yt.get_changes_for_issue(issue_id)
     after_ms = get_in_milliseconds(start) if start else 0
     before_ms = get_in_milliseconds(finish) if finish else sys.maxint
     new_changes = []
     for change in result:
         change_time = change['updated']
         if (change_time > after_ms) and (change_time < before_ms):
             new_changes.append(change)
     return new_changes

def get_in_milliseconds(_datetime):
    return int(round(1e+3*time.mktime(_datetime.timetuple()) + 1e-3*_datetime.microsecond))

class AsymmetricFieldsSynchronizer(object):
    def __init__(self, master, slave, master_executor, slave_executor, fields_to_sync):
        self.master = master
        self.slave = slave
        self.executors = {master : master_executor, slave : slave_executor}
        self.fields_to_sync = fields_to_sync

    def syncFields(self, master_issue_id, slave_issue_id, last_run, current_run):
        #sync fields
        slave_changes = get_issue_changes(self.slave, slave_issue_id, last_run, current_run)
        master_changes = get_issue_changes(self.master, master_issue_id, last_run, current_run)
        #field changes made in master should rewrite any field changes in slave
        changed_fields = self._apply_changes_to_issue(self.slave, self.master, slave_issue_id, master_changes)
        self._apply_changes_to_issue(self.master, self.slave, master_issue_id, slave_changes, fields_to_ignore=changed_fields)

    def _apply_changes_to_issue(self, to_yt, from_yt, issue_id, changes, fields_to_ignore=None):
        if not fields_to_ignore: fields_to_ignore = []
        changed_fields = set()
        for change in changes:
            command, run_as = self._convert_change_to_command(issue_id, change, changed_fields, fields_to_ignore, from_yt, to_yt)
            self.executors[to_yt].executeCommand(issue_id, command, run_as=run_as)
        return changed_fields

    def _convert_change_to_command(self, issue_id, change, changed_fields, fields_to_ignore, from_yt, to_yt):
        run_as = change.updater_name
        self._try_to_sync_user(to_yt, from_yt, run_as)
        command = ''
        for field in change.fields:
            field_name = field.name.lower()
            if field.name != 'links' and field_name in self.fields_to_sync and field_name not in fields_to_ignore:
                try:
                    command += self._create_command(field, field_name, to_yt == self.master)
                    changed_fields.add(field_name)
                except Exception, error:
                    self.executors[to_yt].getLogger().logError(error, issue_id, to_yt, error.message)
        return command, run_as

    def _create_command(self, field, field_name, in_master):
        new_value = [get_event(field)] if in_master and field_name == 'state' else field.new_value
        return self.get_command_set_value_to_field(field_name, new_value)

    def get_command_set_value_to_field(self, field_name, new_value):
        command = ""
        for new_field_value in new_value:
            if new_field_value:
                if field_name == 'priority' and new_field_value in PRIORITY_MAPPING.keys():
                    new_field_value = PRIORITY_MAPPING[new_field_value]
                command += field_name + " " + new_field_value + " "
        return command

    def _try_to_sync_user(self, to_yt, from_yt, login):
        try:
            to_yt.getUser(login)
        except YouTrackException:
            user_to_import = from_yt.getUser(login)
            self.executors[to_yt].executeUserImport(user_to_import)
