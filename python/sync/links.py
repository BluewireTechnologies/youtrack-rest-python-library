import copy

class LinkImporter(object):
    def __init__(self, target, project_id=None, query=None):
        self.target = target
        self.created_issue_ids = self._get_all_issue_ids_set(self.target, project_id, query) if project_id else set([])
        self.links = []
        self.verbose_mode = False

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
        self.created_issue_ids |= self._get_all_issue_ids_set(self.target, project_id) if project_id else set([])

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
    def __init__(self, master_importer, slave_importer, binder):
        self.issue_binder = binder
        self.slaveLinkImporter = slave_importer
        self.masterLinkImporter = master_importer

    def setVerboseMode(self, mode):
        self.slaveLinkImporter.setVerboseMode(mode)
        self.masterLinkImporter.setVerboseMode(mode)

    def collectLinksToSync(self, slave_issue, master_issue):

        slave_links = slave_issue.getLinks(True) if slave_issue else []
        master_links = master_issue.getLinks(True) if master_issue else []

        slave_valid_links = [link for link in slave_links if self.slaveLinkImporter.checkLink(link)]
        master_valid_links =  [link for link in master_links if self.masterLinkImporter.checkLink(link)]

        to_master_links = set([self._convertSlaveLinkForMaster(link) for link in slave_valid_links]) - set(master_valid_links)
        to_slave_links = set([self._convertMasterLinkForSlave(link) for link in master_valid_links]) - set(slave_valid_links)

        self.masterLinkImporter.collectLinks(to_master_links)
        self.slaveLinkImporter.collectLinks(to_slave_links)

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

    def syncCollectedLinks(self):
        self.slaveLinkImporter.importCollectedLinks()
        self.masterLinkImporter.importCollectedLinks()

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