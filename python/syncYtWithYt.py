#import sys
from sync.links import IssueBinder
from sync.logging import Logger
from sync.youtracks import YouTrackSynchronizer
from youtrack import YouTrackException
from youtrack.connection import Connection
from youtrack2youtrack import youtrack2youtrack
from datetime import datetime
from datetime import timedelta
import ConfigParser
import csv

sync_map_file_name = 'sync_map'
config_file_name = 'sync_config'
config_time_format = '%Y-%m-%d %H:%M:%S:%f'
default_last_run = datetime(2012, 1, 1)
section_name = 'Synchronization'
csv.register_dialect('mapper', delimiter=':', quoting=csv.QUOTE_NONE)

def main():

#    try:
#        config_file_name = sys.argv(0)
#    except BaseException:
#        print "Usage: syncYtWithYt config_file_name"
#        return

    config = ConfigParser.RawConfigParser()
    try:
        config.read(config_file_name)
        master_url = config.get(section_name, 'master_url')
        master_root_login = config.get(section_name, 'master_root_login')
        master_root_password = config.get(section_name, 'master_root_password')
        slave_url = config.get(section_name, 'slave_url')
        slave_root_login = config.get(section_name, 'slave_root_login')
        slave_root_password = config.get(section_name, 'slave_root_password')
        project_id = config.get(section_name, 'project_id')
        query = config.get(section_name, 'query')
        fields_to_sync = [field.strip() for field in config.get(section_name, 'fields_to_sync').split(',')]
    except BaseException, e:
        print e
        return

    try:
        last_run_str = config.get(section_name, 'last_run')
        last_run = datetime.strptime(last_run_str, config_time_format)
    except BaseException:
        last_run = default_last_run

    try:
        if config.has_option(section_name, 'debug_mode'):
            debug_mode = config.getboolean(section_name, 'debug_mode')
        else:
            debug_mode = False
    except BaseException, e:
        print e
        print "debug_mode parameter should be set to 'True' or 'False'"
        return

    try:
        slave_to_master_map = read_sync_map()
    except BaseException, e:
        print e
        return

    try:
        sync(master_url,
            master_root_login,
            master_root_password,
            slave_url,
            slave_root_login,
            slave_root_password,
            project_id,
            query,
            fields_to_sync,
            slave_to_master_map,
            last_run,
            debug_mode)

        #query time format has 1 second accuracy, so set last run value
        #as current time shifted by the 1 second forward to avoid
        #applying of changes done by the previous script launch
        last_run = datetime.now() + timedelta(seconds=1)
        config.set(section_name, 'last_run', last_run.strftime(config_time_format))
        with open(config_file_name, 'wb') as configfile:
            config.write(configfile)

    except BaseException, e:
            print e

def read_sync_map():
    try:
        with open(sync_map_file_name, 'r') as sync_map_file:
            reader = csv.reader(sync_map_file, 'mapper')
            result = {}
            for row in reader:
              result[row[0]] = row[1]
            return result
    except IOError:
        with open(sync_map_file_name, 'w') as sync_map_file:
            sync_map_file.write('')
        return {}

def write_sync_map(ids_map):
    with open(sync_map_file_name, 'w') as sync_map_file:
        writer = csv.writer(sync_map_file, 'mapper')
        for key in ids_map.keys():
            writer.writerow([key, ids_map[key]])

def get_project(slave, project_id):
    try:
        return slave.getProject(project_id)
    except YouTrackException:
        return None

def sync(master_url,
         master_root_login,
         master_root_password,
         slave_url,
         slave_root_login,
         slave_root_password,
         project_id,
         query,
         fields_to_sync,
         slave_to_master_map,
         last_run,
         debug_mode):

    issue_binder = IssueBinder(slave_to_master_map)

    master = Connection(master_url, master_root_login, master_root_password)
    slave = Connection(slave_url, slave_root_login, slave_root_password)
    logger = Logger(master, slave, master_root_login, slave_root_login)

    current_run = datetime.now()
    synchronizer = YouTrackSynchronizer(master, slave, logger, issue_binder, project_id, fields_to_sync, query, last_run, current_run)
    synchronizer.setDebugMode(debug_mode)

    try:
        if get_project(slave, project_id):
            synchronizer.sync()
        else:
            youtrack2youtrack(master_url, master_root_login, master_root_password, slave_url, slave_root_login, slave_root_password, [project_id], query)
            synchronizer.syncAfterImport()
    finally:
        logger.finalize()
        #write dictionary of synchronized issues
        write_sync_map(issue_binder.s_to_m)

if __name__ == "__main__":
    main()