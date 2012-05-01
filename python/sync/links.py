class LinkImporter(object):
    def __init__(self, target, project_id=None):
        self.target = target
        self.created_issue_ids = self._get_all_issue_ids_set(self.target, project_id) if project_id else set([])
        self.links = []

    def resetConnections(self, target):
        self.target = target

    def _get_all_issue_ids_set(self, yt, project_id):
        start = 0
        batch = 50
        result = set([])
        while True:
            issues = yt.getIssues(project_id, '', start, batch)
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
                print 'Failed to import link ' + link.source + '->' + link.target + ' because ' + link.target + ' was not imported'
            elif link.source not in self.created_issue_ids:
                print 'Failed to import link ' + link.source + '->' + link.target + ' because ' + link.source + ' was not imported'
            else:
                links_to_import.append(link)
                if len(links_to_import) == maxLinks:
                    print self.target.importLinks(links_to_import)
                    links_to_import = []
        if len(links_to_import):
            print self.target.importLinks(links_to_import)

    def importCollectedLinks(self):
        self.importLinks(self.links)
        self.links = []

class LinkSynchronizer(object):
    def __init__(self, master, slave, binder):
        self.issue_binder = binder
        self.project_id = binder.project_id
        self.master = master
        self.slave = slave
        self.slaveLinkImporter = LinkImporter(slave)
        self.masterLinkImporter = LinkImporter(master)
           
    def resetConnections(self, master, slave):
        self.master = master
        self.slave = slave
        self.slaveLinkImporter.resetConnections(slave)
        self.masterLinkImporter.resetConnections(master)

    def collectLinksToSync(self, slave_issue, master_issue):

        slave_links = slave_issue.getLinks(True) if slave_issue else []
        master_links = master_issue.getLinks(True) if master_issue else []

        #transfer all links to the master notation
        for slave_link in slave_links:
            slave_link.source = self.issue_binder.slaveIssueIdToMasterIssueId(slave_link.source)
            slave_link.target = self.issue_binder.slaveIssueIdToMasterIssueId(slave_link.target)
        slave_links_set = frozenset(slave_links)
        master_links_set = frozenset(master_links)

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
        self.slaveLinkImporter.addAvailableIssuesFrom(self.project_id)
        self.slaveLinkImporter.importCollectedLinks()
        self.masterLinkImporter.addAvailableIssuesFrom(self.project_id)
        self.masterLinkImporter.importCollectedLinks()

class IssueBinder(object):
    def __init__(self, master, slave, project_id, master_sync_field_name):
        self.master = master
        self.slave = slave
        self.project_id = project_id
        self.field_name = master_sync_field_name

    def slaveIssueIdToMasterIssueId(self, slave_issue_id):
        return unicode(self.project_id + "-" + self.slave.getIssue(slave_issue_id)[self.field_name])

    def masterIssueIdToSlaveIssueId(self, master_issue_id):
        return unicode(self.slave.getIssues(self.project_id, self.field_name + ": " + master_issue_id.rpartition('-')[2], 0, 1)[0].id)