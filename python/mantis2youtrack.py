from youtrack.connection import Connection
from mantis.mantisClient import MantisClient
from youtrack import *
from mantis import MantisCustomFieldDef
import sys
import mantis
import mantis.defaultMantis
from StringIO import StringIO
from youtrack.importHelper import *
import youtrack.importHelper

def main() :
    #target_url, target_login, target_pass, mantis_db, mantis_host, mantis_port, mantis_login, mantis_pass = sys.argv[1:9]
    target_url = "http://localhost:8081"
    target_login = "root"
    target_pass = "root"
    mantis_db = "mantisBT"
    mantis_host = "localhost"
    mantis_port = "3306"
    mantis_login = "root"
    mantis_pass = "root"
    #        mantis_product_names = sys.argv[9:]
    mantis_product_names = ["Sandbox"]
    mantis2youtrack(target_url, target_login, target_pass, mantis_db, mantis_host,
                    mantis_port, mantis_login, mantis_pass, mantis_product_names)


def to_yt_user(mantis_user) :
    yt_user = User()
    yt_user.login = mantis_user.user_name
    yt_user.fullName = mantis_user.real_name
    yt_user.email = mantis_user.email
    return yt_user

def to_yt_subsystem(mantis_cat, bundle, value_mapping) :
    name = mantis_cat.name
    if name in value_mapping:
        name = value_mapping[name]
    subsys = bundle.createElement(name)
    subsys.isDefault = False
    assignee = mantis_cat.assignee
    if assignee is not None:
        subsys.owner = assignee
    else :
        subsys.defaultAssignee = ""
    return subsys

def to_yt_version(mantis_version, bundle, value_mapping) :
    name = mantis_version.name
    if name in value_mapping:
        name = value_mapping[name]
    yt_version = bundle.createElement(name)
    yt_version.isReleased = mantis_version.is_released
    yt_version.isArchived = mantis_version.is_obsolete
    yt_version.releaseDate = mantis_version.release_date
    return yt_version

def to_yt_comment(mantis_comment) :
    yt_comment = Comment()
    yt_comment.author = mantis_comment.reporter
    yt_comment.text = mantis_comment.text
    yt_comment.created = mantis_comment.date_submitted
    return yt_comment

def to_yt_issue(mantis_issue, value_sets) :
    issue = Issue()
    issue.numberInProject = mantis_issue.id
    issue.summary = mantis_issue.summary
    # description
    description = mantis_issue.description
    steps_to_reproduce = mantis_issue.steps_to_reproduce
    if (steps_to_reproduce is not None) and (len(steps_to_reproduce.strip()) > 0):
        description = description + "\n Steps to reproduce : \n" + steps_to_reproduce
    additional = mantis_issue.additional_information
    if (additional is not None) and (len(additional.strip()) > 0):
        description = description + "\n Additional information : \n" + additional
    issue.description = description
    issue.created = mantis_issue.date_submitted
    issue.updated = mantis_issue.last_updated
    reporter = mantis_issue.reporter_name
    if reporter in value_sets["user"]:
        issue.reporterName = reporter
    else :
        issue.reporterName = "guest"
    assignee = mantis_issue.handler_name
    if assignee in value_sets["user"]:
        issue.assigneeName = assignee
    issue.comments = []
    for c in mantis_issue.comments :
        issue.comments.append(to_yt_comment(c))
    #Custom fields
    for cf_name in mantis_issue.cf_values:
        if (cf_name == "subproject") and not mantis.CREATE_CF_FOR_SUBPROJECT:
            continue
        values = mantis_issue.cf_values[cf_name]
        for yt_field_name in get_yt_cf_name_from_mantis_cf_name(cf_name):
            if yt_field_name in value_sets :
                field_values = get_yt_values_from_mantis_values(yt_field_name, values)
                value_set = value_sets[yt_field_name]
                issue[yt_field_name] = []
                for value in field_values:
                    if value in value_set:
                        issue[yt_field_name].append(value)
            else:
                issue[yt_field_name] = values
    return issue

def get_bundle_name_for_custom_field(mantis_cf) :
    return "enum_" + str(mantis_cf.field_id)

def get_yt_values_from_mantis_values(yt_field_name, mantis_values):
    if mantis_values is None :
         return None
    if yt_field_name not in mantis.FIELD_VALUES:
        return mantis_values
    values_map = mantis.FIELD_VALUES[yt_field_name]
    values = []
    for value in mantis_values :
        if value in values_map:
            mapped_value = values_map[value]
            if mapped_value is not None:
                values.append(mapped_value)
        else:
            values.append(value)
    return values

def get_yt_cf_name_from_mantis_cf_name(mantis_field_name):
    if mantis_field_name in mantis.FIELD_NAMES:
        return mantis.FIELD_NAMES[mantis_field_name]
    return [mantis_field_name.capitalize()]

def to_yt_link(mantis_link):
    link = Link()
    link.source = "%s-%s" % (mantis_link.source_project_id, mantis_link.source)
    link.target = "%s-%s" % (mantis_link.target_project_id, mantis_link.target)
    link.typeName = mantis.LINK_TYPES[mantis_link.type]
    return link


def create_yt_cfs_with_values(connection, yt_cf_names, mantis_field_values,
                                            attach_bundle_policy = "0", auto_attach = True):
    values_sets = dict([])
    for cf_name in yt_cf_names:
        if mantis_field_values is not None :
            yt_field_values = get_yt_values_from_mantis_values(cf_name, mantis_field_values)
        else:
            yt_field_values = None
        create_custom_field(connection, mantis.FIELD_TYPES[cf_name],
                            cf_name, auto_attach, yt_field_values, attach_bundle_policy)
        if mantis_field_values is not None:
            values_sets[cf_name] = set(yt_field_values)
    return values_sets

def create_custom_fields(connection, mantis_field_name, mantis_field_values = None,
                                       attach_bundle_policy = "0", auto_attach = True) :
    """
    Converts mantis_field_name to yt field name, mantis_field_values to yt field values and creates
    auto attached field with such names and values.

    Args:
        connection: Opened Connection instance.
        mantis_field_name: Name of custom field in mantis.
        mantis_field_values: Values of custom field in mantis. If mantis_field_values in None, bundle is not
            created. If mantis_field_values is empty, empty bundle is created.
        attach_bundle_policy: Should be "0" if bundle must be attached as is and "1" if it should be cloned.
        auto_attach: 

    Returns:
        Map of names and sets of values.
    """
    print "Processing custom field with name [ %s ]" % mantis_field_name.encode('utf-8')
    yt_cf_names = get_yt_cf_name_from_mantis_cf_name(mantis_field_name)
    return create_yt_cfs_with_values(connection, yt_cf_names, mantis_field_values, attach_bundle_policy, auto_attach)


def process_mantis_custom_field(connection, mantis_cf_def) :
    """
    Converts mantis cf to yt cf.

    Args:
        connection: Opened Connection instance.
        mantis_cf_def: definition of cf in mantis.

    Returns:
        Map of names and sets of values.
    """

    value_sets = dict([])
    # get names of custom fields in youtrack that are mapped with this prototype
    for yt_name in get_yt_cf_name_from_mantis_cf_name(mantis_cf_def.name) :
        # calculate type of custom field in youtrack
        yt_cf_type = mantis.CF_TYPES[mantis_cf_def.type]
        if yt_name in mantis.FIELD_TYPES :
            yt_cf_type = mantis.FIELD_NAMES[yt_name]
        # convert mantis values to yt values
        yt_cf_values = get_yt_values_from_mantis_values(yt_name, mantis_cf_def.values)
        create_custom_field(connection, yt_cf_type,yt_name, False, yt_cf_values)
        if yt_cf_values is not None :
            value_sets[yt_name] = set(yt_cf_values)
    return value_sets
            


def create_auto_attached_bundle_custom_fields(connection, mantis_field_name, mantis_field_values,
                                                mantis_value_to_yt_value, attach_bundle_policy = "0"):
    """
    Converts mantis_field_name to youtrack field names, then converts mantis_field_values to youtrack
    value names, adds them to bundles of created fields using mantis_value_to_yt_value method

    Args:
        connection: Opened Connection instance.
        mantis_field_name: Name of cf in mantis.
        mantis_field_values: Values in custom field in mantis. If field do not have values, it should be empty
        mantis_value_to_yt_value: Method that accepts mantis_value and returns youtrack field value.
        attach_bundle_policy: Should be "0" if bundle must be attached as is and "1" if it should be cloned.

    Returns:
        Mapping between names of custom fields in yt and values
    """
    yt_field_names = get_yt_cf_name_from_mantis_cf_name(mantis_field_name)
    create_yt_cfs_with_values(connection, yt_field_names, [], attach_bundle_policy)
    value_sets = dict([])
    for name in yt_field_names:
        bundle = connection.getBundle(mantis.FIELD_TYPES[name], connection.getCustomField(name).defaultBundle)
        #yt_field_value_names = get_yt_values_from_mantis_values(name, mantis_field_values)
        values_mapping = dict([]) if name not in mantis.FIELD_VALUES else mantis.FIELD_VALUES[name]
        values_to_add = [mantis_value_to_yt_value(value, bundle, values_mapping)
                         for value in mantis_field_values]
        add_values_to_bundle_safe(connection, bundle, values_to_add)
        value_sets[name] = [value.name for value in values_to_add]
    return value_sets

def attach_field_to_project(connection, project_id, mantis_field_name) :
    yt_field_names = get_yt_cf_name_from_mantis_cf_name(mantis_field_name)
    for name in yt_field_names:
        project_field = connection.getCustomField(name)
        params = dict([])
        if hasattr(project_field, "defaultBundle"):
            params["bundle"] = project_field.defaultBundle
        connection.createProjectCustomFieldDetailed(str(project_id), name, u"No " + name, params)

def add_values_to_fields(connection, project_id, mantis_field_name, values, mantis_value_to_yt_value) :
    """
    Adds values to custom fields, which are mapped with mantis_field_name field.

    Args:
        connection: Opened Connection instance.
        project_id: Id of project to add values to.
        mantis_field_name: name of cf in Mantis.
        values: Values to add to field in Mantis.

    Returns:
        Map of yt field names and yt field values.

    """
    value_sets = dict([])
    for field_name in get_yt_cf_name_from_mantis_cf_name(mantis_field_name) :
        pcf = connection.getProjectCustomField(str(project_id), field_name)
        if hasattr(pcf, "bundle"):
            value_mapping = dict([])
            if field_name in mantis.FIELD_VALUES:
                value_mapping = mantis.FIELD_VALUES[field_name]
            bundle = connection.getBundle(pcf.type[0:-3], pcf.bundle)
            yt_values = [mantis_value_to_yt_value(value, bundle, value_mapping) for value in values]
            value_names = [elem.name for elem in yt_values]
            value_sets[field_name] = set(value_names)
            add_values_to_bundle_safe(connection, bundle, yt_values)
    return value_sets


def to_yt_state(state_name, bundle, value_mapping) :
    if state_name in value_mapping:
        state_name = value_mapping[state_name]
    state = bundle.createElement(state_name)
    state.isResolved = True
    return state

def mantis2youtrack(target_url, target_login, target_pass, mantis_db_name, mantis_db_host,  mantis_db_port,
                    mantis_db_login, mantis_db_pass, mantis_project_names) :
    print "target_url             : " + target_url
    print "target_login           : " + target_login
    print "target_pass            : " + target_pass
    print "mantis_db_name         : " + mantis_db_name
    print "mantis_db_host         : " + mantis_db_host
    print "mantis_db_port         : " + mantis_db_port
    print "mantis_db_login        : " + mantis_db_login
    print "mantis_db_pass         : " + mantis_db_pass
    print "mantis_project_names   : " + repr(mantis_project_names)

    #connacting to yt
    target = Connection(target_url,target_login, target_pass)
    #connacting to mantis
    client = MantisClient(mantis_db_host, int(mantis_db_port), mantis_db_login,
                          mantis_db_pass, mantis_db_name, mantis.CHARSET)
    if not len(mantis_project_names):
        print "You should declarer at least one project to import"
        sys.exit()

    value_sets = dict([])

    print "Importing users"
    yt_users = []
    value_sets["user"] = set([])
    for user in client.get_mantis_users() :
        print "Processing user [ %s ]" % user.user_name
        value_sets["user"].add(user.user_name)
        yt_users.append(to_yt_user(user))
    target.importUsers(yt_users)
    print "Importing users finished"

    print "Creating custom fields definitions"
    value_sets.update(create_custom_fields(target, u"priority", mantis.PRIORITY_VALUES.values()))
    value_sets.update(create_custom_fields(target, u"severity", mantis.SEVERITY_VALUES.values()))
    value_sets.update(create_custom_fields(target, u"category", ["No subsystem"], "1"))
    value_sets.update(create_custom_fields(target, u"version", [], "1"))
    value_sets.update(create_custom_fields(target, u"fixed_in_version", [], "1"))
    value_sets.update(create_custom_fields(target, u"build", [], "1"))
    value_sets.update(create_custom_fields(target, u"platform"))
    value_sets.update(create_custom_fields(target, u"os"))
    value_sets.update(create_custom_fields(target, u"os_build"))
    value_sets.update(create_custom_fields(target, u"due_date"))
    value_sets.update(create_custom_fields(target, u"Reproducibility", mantis.REPRODUCIBILITY_VALUES.values()))

    #create custom field for target version
    field = None
    try:
        field = target.getCustomField("Fix versions")
    except YouTrackException:
        pass
    if field is not None:
        if hasattr(field, "defaultBundle"):
            bundle = field.bundle
            for name in get_yt_cf_name_from_mantis_cf_name("target_version"):
                target.createCustomFieldDetailed(name, mantis.FIELD_TYPES[name], False, True, True,
                        {"defaultBundle" : bundle, "attachBundlePolicy" : "1"})

    value_sets.update(create_auto_attached_bundle_custom_fields(target, u"status", mantis.STATUS_VALUES.values(),
                                              lambda status, bundle, value_mapping :
                                              to_yt_state(status, bundle, value_mapping)))

    value_sets.update(create_auto_attached_bundle_custom_fields(target, u"resolution", mantis.RESOLUTION_VALUES.values(),
                                              lambda resolution, bundle, value_mapping :
                                              to_yt_state(resolution, bundle, value_mapping)))

    if mantis.CREATE_CF_FOR_SUBPROJECT :
        value_sets.update(create_custom_fields(target, u"subproject", [], "1"))

    handler_field_name = u"handler"
    value_sets.update(create_custom_fields(target, handler_field_name, [], "1"))
    for name in get_yt_cf_name_from_mantis_cf_name(handler_field_name) :
        value_sets[name] = value_sets["user"]

    # adding some custom fields that are predefined in mantis
    project_ids = []
    for name in mantis_project_names :
        project_ids.append(client.get_project_id_by_name(name))

    custom_fields = client.get_mantis_custom_fields(project_ids)

    for cf_def in custom_fields :
        print "Processing custom field [ %s ]" % cf_def.name.encode('utf-8')
        value_sets.update(process_mantis_custom_field(target, cf_def))

    print "Creating custom fields definitions finished"

    for name in mantis_project_names :
        project_id = int(client.get_project_id_by_name(name))
        print "Creating project [ %s ] with name [ %s ]" % (project_id, name)
        try :
            target.getProject(str(project_id))
        except YouTrackException:
            target.createProjectDetailed(str(project_id), name, client.get_project_description(project_id), target_login)

        print "Importing components to project [ %s ]" % project_id
        value_sets.update(add_values_to_fields(target, project_id, u"category",
                                               client.get_mantis_categories(project_id),
                                               lambda component, yt_bundle, value_mapping:
                                               to_yt_subsystem(component, yt_bundle, value_mapping)))
        print "Importing components to project [ %s ] finished" % project_id

        print "Importing versions to project [ %s ]" % project_id
        mantis_versions = client.get_mantis_versions(project_id)
        value_sets.update(add_values_to_fields(target,project_id, u"version", mantis_versions,
                                               lambda version, yt_bundle, value_mapping:
                                               to_yt_version(version, yt_bundle, value_mapping)))

        value_sets.update(add_values_to_fields(target, project_id, u"fixed_in_version",
                                               mantis_versions,
                                               lambda version, yt_bundle, value_mapping:
                                               to_yt_version(version, yt_bundle, value_mapping)))

        for name in get_yt_cf_name_from_mantis_cf_name("target_version"):
            value_sets[name] = value_sets["Fix versions"]

        print "Importing versions to project [ %s ] finished" % project_id

        print "Attaching custom fields to project [ %s ]" % project_id
        cf_ids = client.get_custom_fields_attached_to_project(project_id)

        for cf in custom_fields :
            if cf.field_id in cf_ids:
               attach_field_to_project(target, project_id, cf.name)

        if mantis.CREATE_CF_FOR_SUBPROJECT:
            value_sets.update(add_values_to_fields(target, project_id, u"subproject",
                                                   client.get_mantis_subprojects(project_id),
                                                   lambda sp_name, yt_bundle, value_mapping:
                                                   yt_bundle.createElement(sp_name) if sp_name not in value_mapping else
                                                   yt_bundle.createElement(value_sets[sp_name])))
        print "Attaching custom fields to project [ %s ] finished" % project_id


        print "Importing issues to project [ %s ]" % project_id
        mantis_issues = client.get_mantis_issues(project_id)
        yt_issues = []
        max_count = 100
        for issue in mantis_issues  :
            #print "Processing issue [ %s ]" % str(issue.id)
            yt_issues.append(to_yt_issue(issue, value_sets))
            if len(yt_issues) >= max_count:
                print target.importIssues(str(project_id), name + "Assignees", yt_issues)
                yt_issues = []
        target.importIssues(str(project_id), str(project_id) + "Assignees", yt_issues)
        print "Importing issues to project [ %s ] finished" % project_id

        print "Importing issue attachments to project [ %s ]" % project_id
        mantis_attachments = client.get_mantis_attachments(project_id)
        for attachment in mantis_attachments  :
            print "Processing issue attachment [ %s ]" % str(attachment.id)
            content = StringIO(attachment.content)
            authorLogin = client.get_user_name_by_id(attachment.user_id)
            target.createAttachment("%s-%s" %(project_id,attachment.bug_id),attachment.filename, content, authorLogin, attachment.file_type,None,
                                    str(attachment.date_added * 1000))
        print "Importing issue attachments to project [ %s ] finished" % project_id

        print "Importing tags to issues from project [ %s ]" % project_id
        for issue in mantis_issues :
            print "Processing tags for issue [ %s ]" % str(issue.id)
            for tag in issue.tags :
                print "Processing tag [ %s ]" % tag.encode('utf8')
                target.executeCommand(str(project_id) + "-" + str(issue.id), "tag " + tag.encode('utf8'))
        print "Importing tags to issues from project [ %s ] finished" % project_id

    print "Importing issue links"
    mantis_issue_links = client.get_issue_links()
    yt_issue_links = []
    for link in mantis_issue_links  :
        print "Processing issue link for source issue [ %s ]" % str(link.source)
        yt_issue_links.append(to_yt_link(link))
    print target.importLinks(yt_issue_links)
    print "Importing issue links finished"


if __name__ == "__main__":
    main()