CF_TYPES = dict([])
LINK_TYPES = dict([])
CREATE_CF_FOR_SUBPROJECT = True
CHARSET = "cp866"
FIELD_NAMES = dict([])
FIELD_TYPES = dict([])
FIELD_VALUES = dict([])


PRIORITY_VALUES = {
    10 : "none",
    20 : "low",
    30 : "normal",
    40 : "high",
    50 : "urgent",
    60 : "immediate"
}

SEVERITY_VALUES = {
    10 : "Feature",
    20 : "Trivial",
    30 : "Text",
    40 : "Tweak",
    50 : "Minor",
    60 : "Major",
    70 : "Crash",
    80 : "Block",
    90 : "Super Blocker"
}

REPRODUCIBILITY_VALUES = {
    10  : "Always",
    30  : "Sometimes",
    50  : "Random",
    70  : "Have not tried",
    90  : "Unable to reproduce",
    100 : "N/A"
}

STATUS_VALUES = {
    10 : "new",
    20 : "feedback",
    30 : "acknowledged",
    40 : "confirmed",
    50 : "assigned",
    60 : "resolved",
    70 : "closed",
    75 : "some_status_3",
    80 : "some_status_1",
    90 : "some_status_2"
}

RESOLUTION_VALUES = {
    10 : "open",
    20 : "fixed",
    30 : "reopened",
    40 : "unable to reproduce",
    50 : "not fixable",
    60 : "duplicate",
    70 : "no change required",
    80 : "suspended",
    90 : "won't fix"
}

class MantisUser(object) :

    def __init__(self, name) :
        self.user_name = name
        self.real_name = ""
        self.email = ""

class MantisIssue(object) :

    def __init__(self, id) :
        self.id = str(id)
        self.subproject_name = ""
        self.reporter_name = ""
        self.handler_name = ""
        self.priority = None
        self.severity = None
        self.reproducibility = None
        self.status = None
        self.resolution = None
        self.description = ""
        self.steps_to_reproduce = ""
        self.additional_information = ""
        self.os = ""
        self.os_build = ""
        self.platform = ""
        self.version = ""
        self.fixed_in_version = ""
        self.build = ""
        self.summary = ""
        self.target_version = ""
        self.category = ""
        self.date_submitted = None
        self.due_date = None
        self.last_updated = None
        self.cf_values = dict([])
        self.tags = []
        self.comments = []

class MantisCategory(object) :
    def __init__(self, name) :
        self.name = name
        self.assignee = None

class MantisVersion(object) :
    def __init__(self, name) :
        self.name = name
        self.is_released = True
        self.is_obsolete = False

class MantisCustomFieldDef(object) :
    def __init__(self, id) :
        self.name = None
        self.type = None
        self.values = None
        self.field_id = id
        self.default_value = None

class MantisComment(object) :
    def __init__(self) :
        self.reporter = ""
        self.date_submitted = None
        self.text = ""

class MantisIssueLink(object) :
    def __init__(self, source, target, type):
        self.source = source
        self.target = target
        self.source_project_id = None
        self.target_project_id = None
        self.type = type

class MantisAttachment(object):
    def __init__(self, id, cnx):
        self.id = id
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM mantis_bug_file_table WHERE id = %s" %(id,))
        row = cursor.fetchone()
        self.bug_id = row["bug_id"]
        project_id_cursor = cnx.cursor()
        project_id_cursor.execute("SELECT project_id FROM mantis_bug_table WHERE id=%s", (self.bug_id,))
        self.project_id = project_id_cursor.fetchone()["project_id"]
        self.title = row["title"]
        self.filename = row["filename"]
        self.file_type = row["file_type"]
        self.content = row["content"]
        self.user_id = row["user_id"]
        self.date_added = row["date_added"]
