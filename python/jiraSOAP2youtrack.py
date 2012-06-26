from SOAPpy.Types import typedArrayType
import jira
from jira.jiraSoapClient import JiraSoapClient
from youtrack import Issue, YouTrackException
from youtrack.connection import Connection
from youtrack.importHelper import create_bundle_safe

def to_unix_date(time_tuple):
    return "27000000"

def create_user(target, value):
    try:
        target.createUserDetailed(value.replace(' ', '_'), value, 'fake_email', 'fake_jabber')
    except YouTrackException, e:
        print(str(e))


def get_yt_field_name(jira_name):
    if jira_name in jira.FIELD_NAMES:
        return jira.FIELD_NAMES[jira_name]
    return jira_name


def get_yt_field_type(jira_name):
    if jira_name in jira.SOAP_TYPES:
        return jira.SOAP_TYPES[jira_name]
    return None

def create_value(target, value, field_name, field_type, project_id):
    if (field_type is not None) and field_type.startswith('user'):
        create_user(target, value)
        value = value.replace(' ', '_')
    if field_name in jira.EXISTING_FIELDS:
        return
    if field_name.lower() not in [field.name.lower() for field in target.getProjectCustomFields(project_id)]:
        if field_name.lower() not in [field.name.lower() for field in target.getCustomFields()]:
            target.createCustomFieldDetailed(field_name, field_type, False, True, False, {})
        if field_type in ['string', 'date', 'integer']:
            target.createProjectCustomFieldDetailed(project_id, field_name, "No " + field_name)
        else:
            bundle_name = field_name + " bundle"
            create_bundle_safe(target, bundle_name, field_type)
            target.createProjectCustomFieldDetailed(project_id, field_name, "No " + field_name, {'bundle': bundle_name})
    if field_type in ['string', 'date', 'integer']:
        return
    project_field = target.getProjectCustomField(project_id, field_name)
    bundle = target.getBundle(field_type, project_field.bundle)
    try:
        if isinstance(value, str):
            target.addValueToBundle(bundle, value)
        elif hasattr(value, 'name'):
            target.addValueToBundle(bundle, value.name)
        elif hasattr(value, 'value'):
            target.addValueToBundle(bundle, value.value)
    except YouTrackException:
        pass

def get_value_presentation(field_type, value):
    if field_type == 'date':
        return to_unix_date(value)
    if field_type == 'integer':
        return str(value)
    if field_type == 'string':
        return value
    if hasattr(value, 'name'):
        return value.name
    if (field_type is not None) and field_type.startswith('user'):
        return value.replace(' ', '_')
    return value

def to_yt_issue(target, jira_issue):
    issue = Issue()
    issue['comments']= []

    # process issue id
    issue.numberInProject = jira_issue.key[(jira_issue.key.find('-') + 1):]

    # process issue fields
    for jira_name in ["priority", "updated", "description", "created", "type", "reporter", "fixVersions",
                       "assignee", "status", "components", "affectsVersions", "summary", "resolution",
                       "duedate"]:
        field_name = get_yt_field_name(jira_name)
        field_type = get_yt_field_type(field_name)

        if field_name is not None:
            value = getattr(jira_issue, jira_name)
            if value is not None:
                if isinstance(value, typedArrayType):
                    if len(value):
                        issue[field_name] = []
                        for v in value:
                            create_value(target, v, field_name, field_type, jira_issue.project)
                            issue[field_name].append(get_value_presentation(field_type, v))
                else:
                    create_value(target, value, field_name, field_type, jira_issue.project)
                    issue[field_name] = get_value_presentation(field_type, value)

    # process custom fields
    for custom_field in jira_issue.customFieldValues:
        field_name = get_yt_field_name(custom_field.customFieldId)
        field_value = custom_field.values
        field_type = get_yt_field_type(field_name)
        if (field_name is not None) and (field_type is not None):
            pass

    return issue



source = JiraSoapClient("jira url", "jira login", "jira pass")
target = Connection('http://localhost:8081', 'root', 'root')

project_ids = {'ACS'        : 100,
               'ASL'        : 100,
               'BLZ'        : 100,
               'CGM'        : 100,
               'DURANGO'    : 100,
               'FCM'        : 100,
               'FLEXDMV'    : 100,
               'FLEXDOCS'   : 100,
               'FLEXENT'    : 100,
               'SDK'        : 100,
               'FLEXPMD'    : 100,
               'FXU'        : 100
}


for p_id in project_ids:
    target.createProjectDetailed(p_id, p_id, "", "root")
    step = 10
    for i in range(0, project_ids[p_id] / step + 1):
        yt_issues = []
        for issue in source.get_issues(p_id, i * 10, (i + 1) * 10):
            yt_issues.append(to_yt_issue(target, issue))
        target.importIssues(p_id, p_id + " assignees", yt_issues)