from youtrack import YouTrackException

LOGGED_COMMENT_LENGTH = 10

class SafeCommandExecutor(object):
    def __init__(self, yt, logger):
        self.yt = yt
        self.logger = logger
        self.debug_mode = False

    def setDebugMode(self, on):
        self.debug_mode = on

    def executeCommand(self, issue_id, command, comment=None, run_as=None):
        if command != '':
            try:
                if not self.debug_mode:
                    self.yt.executeCommand(issue_id, command, comment=comment, run_as=run_as)
                if comment:
                    self.logger.logAction(issue_id, self.yt, 'added comment: \"' + comment[0:LOGGED_COMMENT_LENGTH] + '...\"', run_as)
                else:
                    self.logger.logAction(issue_id, self.yt, 'applied command: \"' + command + '\"', run_as)
            except Exception, e:
                self.logger.logError(e, issue_id, self.yt, 'failed to apply command: \"' + command + '\"', run_as)

    def executeUserImport(self, user):
        if user:
            try:
                if not self.debug_mode:
                    self.yt.importUsers([user])
                self.logger.logAction('Import user', self.yt, 'imported user: \"' + str(user.login) + '\"')
            except YouTrackException, e:
                self.logger.logError(e, 'Import user', self.yt, 'failed to import user: \"' + user.login + '\" - could not find in opposite youtrack')

    def createIssue(self, project_id, summary, description, issue_from_id):
        try:
            created_issue_id = 'DEBUG'
            if not self.debug_mode:
                created_message = self.yt.createIssue(project_id, None, summary, description)
                created_issue_id = project_id + '-' + created_message.rpartition('-')[2]
                #fail if summary or description are too long or can't convert to unicode params
            self.logger.logAction(str(issue_from_id) + '->' + created_issue_id, self.yt, 'created')
            return None if self.debug_mode else created_issue_id
        except Exception, e:
            self.logger.logError(e, str(issue_from_id) + '->?', self.yt, 'failed to create' )
            return None

    def importLinks(self, links, permitted_issue_ids):
        maxLinks = 100
        links_to_import = []
        for link in links:
            if link.target not in permitted_issue_ids:
                message = 'failed to import link ' + self._getPrettyLink(link)  + ' because ' + link.target + ' was not imported'
                self.logger.logError(None, 'Links', self.yt, message)
            elif link.source not in permitted_issue_ids:
                message = 'failed to import link ' + self._getPrettyLink(link) + ' because ' + link.source + ' was not imported'
                self.logger.logError(None, 'Links', self.yt, message)
            else:
                links_to_import.append(link)
                if len(links_to_import) == maxLinks:
                    self._import_links_batch(links_to_import)
                    links_to_import = []
        if len(links_to_import):
            self._import_links_batch(links_to_import)

    def _import_links_batch(self, links_to_import):
        if not self.debug_mode:
            self.yt.importLinks(links_to_import)
        for link in links_to_import:
            message = 'imported ' + self._getPrettyLink(link)
            self.logger.logAction('Links', self.yt, message)

    def _getPrettyLink(self, link):
           return link.typeName + ' link: ' + link.source + '->' + link.target

    def getLogger(self):
        return self.logger