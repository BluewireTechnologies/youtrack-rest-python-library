import copy

class LinkImporter(object):
    def __init__(self, target, project_id=None, query=None):
        self.target = target
        self.created_issue_ids = self._get_all_issue_ids_set(self.target, project_id, query) if project_id else set([])
        self.links = []
        self.verbose_mode = False
        self.target_name = "youtrack"
        self.header = "[Link importer]"

    def setVerboseMode(self, mode):
        self.verbose_mode = mode

    def resetConnections(self, target):
        self.target = target

    def setYoutrackName(self, name):
        self.target_name = name

    def setLogHeader(self, header):
        self.header = header

    def _get_all_issue_ids_set(self, yt, project_id, query):
        if not query: query = ''
        start = 0
        batch = 50
        result = set([])
        while True:
            issues = yt.getIssues(project_id, query, start, batch)
            if not len(issues): break
            for issue in issues:
                result.add(issue.id)
            start += batch
        return result

    def resetAvailableIssues(self):
        self.created_issue_ids = set([])

    def addAvailableIssuesFrom(self, project_id):
        self.created_issue_ids |= self._get_all_issue_ids_set(self.target, project_id, None) if project_id else set([])

    def addAvailableIssues(self, issues):
        self.created_issue_ids |= set([issue.id for issue in issues])

    def addAvailableIssue(self, issue):
        self.created_issue_ids.add(issue.id)

    def collectLinks(self, links):
        self.links += links

    def importLinks(self, links):
        maxLinks = 100
        links_to_import = []
        for link in links:
            if link.target not in self.created_issue_ids:
                print self.header + ' failed to import link ' + self._getPrettyLink(link) + ' to ' + self.target_name + ' because ' + link.target + ' was not imported'
            elif link.source not in self.created_issue_ids:
                print self.header + 'failed to import link ' + self._getPrettyLink(link) + ' to ' + self.target_name + ' because ' + link.source + ' was not imported'
            else:
                links_to_import.append(link)
                if len(links_to_import) == maxLinks:
                    self._import_links_batch(links_to_import)
                    links_to_import = []
        if len(links_to_import):
            self._import_links_batch(links_to_import)

    def _import_links_batch(self, links_to_import):
        if not self.verbose_mode:
            self.target.importLinks(links_to_import)
        for link in links_to_import:
            print self.header + ' imported ' + self._getPrettyLink(link) + ' to ' + self.target_name

    def importCollectedLinks(self):
        self.importLinks(self.links)
        self.links = []

    def _getPrettyLink(self, link):
        return link.typeName + ' link: ' + link.source + '->' + link.target

    def checkLink(self, link):
        return link.source in self.created_issue_ids and link.target in self.created_issue_ids

class LinkSynchronizer(object):
    def __init__(self, master_executor, slave_executor, binder):
        self.issue_binder = binder
        self.slaveExecutor = slave_executor
        self.masterExecutor = master_executor
        self.master_links = []
        self.slave_links = []

    def collectLinksToSyncById(self, master_issue_id, slave_issue_id):

        slave_links = self.slaveExecutor.yt.getLinks(slave_issue_id, True) if slave_issue_id else []
        master_links = self.masterExecutor.yt.getLinks(master_issue_id, True) if master_issue_id else []

        to_master_links = set([self._convertSlaveLinkForMaster(link) for link in slave_links if self.check_slave_link(link)]) - set(master_links)
        to_slave_links = set([self._convertMasterLinkForSlave(link) for link in master_links if self.check_master_link(link)]) - set(slave_links)

        self.master_links += to_master_links
        self.slave_links += to_slave_links

    def _convertSlaveLinkForMaster(self, slave_link):
        link_copy = copy.copy(slave_link)
        link_copy.source = self.issue_binder.slaveIssueIdToMasterIssueId(slave_link.source)
        link_copy.target = self.issue_binder.slaveIssueIdToMasterIssueId(slave_link.target)
        return link_copy

    def _convertMasterLinkForSlave(self, master_link):
        link_copy = copy.copy(master_link)
        link_copy.source = self.issue_binder.masterIssueIdToSlaveIssueId(master_link.source)
        link_copy.target = self.issue_binder.masterIssueIdToSlaveIssueId(master_link.target)
        return link_copy

    def check_slave_link(self, link):
        return self.issue_binder.checkSlaveId(link.source) and self.issue_binder.checkSlaveId(link.target)

    def check_master_link(self, link):
        return self.issue_binder.checkMasterId(link.source) and self.issue_binder.checkMasterId(link.target)

    def syncCollectedLinks(self):
        self.slaveExecutor.importLinks(self.slave_links, self.issue_binder.getPermittedSlaveIds())
        self.masterExecutor.importLinks(self.master_links, self.issue_binder.getPermittedMasterIds())
        self.slave_links = []
        self.master_links = []

class IssueBinder(object):
    def __init__(self, s_to_m):
        self.s_to_m = copy.copy(s_to_m)
        self.m_to_s = {}
        for s_id , m_id in s_to_m.items():
            self.m_to_s[m_id] = s_id

    def slaveIssueIdToMasterIssueId(self, slave_issue_id):
        return unicode(self.s_to_m[str(slave_issue_id)])

    def masterIssueIdToSlaveIssueId(self, master_issue_id):
        return unicode(self.m_to_s[str(master_issue_id)])

    def addBinding(self, master_id, slave_id):
        self.s_to_m[slave_id] = master_id
        self.m_to_s[master_id] = slave_id

    def getPermittedMasterIds(self):
        return self.m_to_s.keys()

    def getPermittedSlaveIds(self):
        return self.s_to_m.keys()

    def checkSlaveId(self, id):
        return self.s_to_m.has_key(id)

    def checkMasterId(self, id):
        return self.m_to_s.has_key(id)