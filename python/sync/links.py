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
                print 'Failed to import link ' + self._getPrettyLink(link) + ' because ' + link.target + ' was not imported'
            elif link.source not in self.created_issue_ids:
                print 'Failed to import link ' + self._getPrettyLink(link) + ' because ' + link.source + ' was not imported'
            else:
                links_to_import.append(link)
                if len(links_to_import) == maxLinks:
                    if not self.verbose_mode:
                        self.target.importLinks(links_to_import)
                    for link in links_to_import:
                        print 'Import ' + self._getPrettyLink(link)
                    links_to_import = []
        if len(links_to_import):
            if not self.verbose_mode:
                self.target.importLinks(links_to_import)
            for link in links_to_import:
                print 'Import ' + self._getPrettyLink(link)

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

        #transfer all links to the master notation
        for slave_link in slave_valid_links:
            slave_link.source = self.issue_binder.slaveIssueIdToMasterIssueId(slave_link.source)
            slave_link.target = self.issue_binder.slaveIssueIdToMasterIssueId(slave_link.target)
        slave_links_set = set(slave_valid_links)
        master_links_set = set(master_valid_links)

        if len(slave_links):
            links_to_ba_added_in_master = slave_links_set - master_links_set
            self.masterLinkImporter.collectLinks(links_to_ba_added_in_master)

        if len(master_links):
            links_to_ba_added_in_slave = master_links_set - slave_links_set
            # transfer links to be added in slave back to the slave notation
            for link_to_be_added in links_to_ba_added_in_slave:
                link_to_be_added.source = self.issue_binder.masterIssueIdToSlaveIssueId(link_to_be_added.source)
                link_to_be_added.target = self.issue_binder.masterIssueIdToSlaveIssueId(link_to_be_added.target)
            self.slaveLinkImporter.collectLinks(links_to_ba_added_in_slave)

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