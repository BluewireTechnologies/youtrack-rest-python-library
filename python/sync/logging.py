from datetime import datetime

LOGGING = True
log_file_name_format = 'log_%d_%m_%Y'
error_file_name_format = 'error_%d_%m_%Y'
MASTER_NAME = "Master"
SLAVE_NAME = "Slave"
UNDEFINED = "Undefined"

class Logger(object):
    def __init__(self, master, slave, master_root_login, slave_root_login):
        today = datetime.now()
        self.log_file = open(today.strftime(log_file_name_format), 'w')
        self.error_file = open(today.strftime(error_file_name_format), 'w')
        self.master = master
        self.slave = slave
        self.master_root_login = master_root_login
        self.slave_root_login = slave_root_login


    def logAction(self, action_name, yt, message, run_as=None):
        line = self._prepare_line(action_name, yt, message, run_as)
        print line
        try:
            if LOGGING: self.log_file.write(str(line) + '\n')
        except UnicodeError, e:
            print e

    def logError(self, error, action_name, yt, message, run_as=None):
        if LOGGING:
            line = self._prepare_line(action_name, yt, message, run_as)
            try:
                self.log_file.write(str(line) + '\n')
                self.error_file.write(str(line) + '\n')
                self.error_file.write(str(error) + '\n')
                self.error_file.write('---------------------------------------------------------\n')
                print line
                print error
            except UnicodeError, e:
                print e

    def finalize(self):
        self.log_file.close()
        self.error_file.close()

    def _prepare_line(self, action_name, yt, message, run_as):
        yt_name = UNDEFINED if None else MASTER_NAME if yt == self.master else SLAVE_NAME
        user_login = (self.master_root_login if yt == self.master else self.slave_root_login) if run_as is None else run_as
        return '[Sync, ' + action_name + ' in ' + yt_name + '] ' + message + ' on behalf of ' + user_login