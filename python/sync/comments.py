from youtrack import YouTrackException

COMPARISON_LENGTH = 10
COMMAND = 'comment'

class CommentSynchronizer(object):
    def __init__(self, master, slave, master_executor, slave_executor):
        self.master = master
        self.slave = slave
        self.executors = {master : master_executor, slave : slave_executor}

    def syncComments(self, master_id, slave_id):
        slave_comments = self.slave.getComments(slave_id)
        master_comments = self.master.getComments(master_id)
        if len(slave_comments) or len(master_comments):
            master_texts = set([cm.text[0:COMPARISON_LENGTH] for cm in master_comments])
            slave_texts = set([cm.text[0:COMPARISON_LENGTH] for cm in slave_comments])
            slave_unique = [cm for cm in slave_comments if cm.text[0:COMPARISON_LENGTH] not in master_texts]
            master_unique = [cm for cm in master_comments if cm.text[0:COMPARISON_LENGTH] not in slave_texts]
            for cm in slave_unique:
                self._sync_comment(self.master, self.slave, master_id, cm.text, cm.author)
            for cm in master_unique:
                self._sync_comment(self.slave, self.master, slave_id, cm.text, cm.author)

    def _sync_comment(self, to_yt, from_yt, issue_id, comment_text, run_as):
        if comment_text is not None and comment_text != '':
            self._try_to_sync_user(to_yt, from_yt, run_as)
            self.executors[to_yt].executeCommand(issue_id, COMMAND, comment=comment_text, run_as=run_as)

    def _try_to_sync_user(self, to_yt, from_yt, login):
        try:
            to_yt.getUser(login)
        except YouTrackException:
            user_to_import = from_yt.getUser(login)
            self.executors[to_yt].executeUserImport(user_to_import)
