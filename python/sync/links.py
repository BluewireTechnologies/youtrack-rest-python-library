class LinkImporter(object):
    def __init__(self, source, target, project_id=None):
        self.source = source
        self.target = target
        self.created_issue_ids = self._get_all_issue_ids_set(self.target, project_id) if project_id else set([])
        self.links = []

    def resetConnections(self, source, target):
        self.source = source
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
        return result

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
