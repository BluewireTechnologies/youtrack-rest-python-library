import youtrack
from youtrack.connection import Connection
from bugzilla.bzClient import Client
from youtrack import *
from StringIO import StringIO
import bugzilla.defaultBzMapping
import bugzilla
import sys
from youtrack.importHelper import create_custom_field, process_custom_field

def main():
    target_url = "http://localhost:8081"
    target_login = "root"
    target_pass = "root"
    bz_db = "bugs"
    bz_host = "localhost"
    bz_port = 3306
    bz_login = "root"
    bz_pass = "root"
    bz_product_names = ["Botsman2", "BZProduct"]
    try:
    #        target_url, target_login, target_pass, bz_db, bz_host, bz_port, bz_login, bz_pass = sys.argv[1:9]
    #        bz_product_names = sys.argv[9:]
        pass
    except:
        sys.exit()
    bugzilla2youtrack(target_url, target_login, target_pass, bz_db, bz_host, bz_port, bz_login, bz_pass,
        bz_product_names)


def to_yt_user(bz_user):
    user = User()
    user.login = bz_user.login
    user.email = bz_user.email
    user.fullName = bz_user.full_name
    return user


def to_unix_date(value):
    return str(value * 1000)


def import_single_user(bz_user, target):
    target.importUsers([to_yt_user(bz_user)])


def to_yt_comment(bz_comment, target):
    comment = Comment()
    if bz_comment.reporter != "":
        import_single_user(bz_comment.reporter, target)
        comment.author = bz_comment.reporter.login
    else:
        comment.author = "guest"
    if bz_comment.content != "":
        comment.text = bz_comment.content
    else:
        return None
    comment.created = to_unix_date(bz_comment.time)
    return comment


def to_yt_issue_link_type(bz_link_type):
    link_type = IssueLinkType()
    link_type.name = bz_link_type.name
    if bz_link_type.description != "":
        link_type.outwardName = bz_link_type.description
        link_type.inwardName = "incoming " + bz_link_type.description
    else:
        link_type.outwardName = bz_link_type.name
        link_type.inwardName = "incoming " + bz_link_type.name
    link_type.directed = True
    return link_type


def to_yt_issue_link(bz_issue_link):
    link = Link()
    link.typeName = bz_issue_link.name
    link.source = str(bz_issue_link.target_product_id) + "-" + str(bz_issue_link.target)
    link.target = str(bz_issue_link.source_product_id) + "-" + str(bz_issue_link.source)
    return link


def add_value_to_field(field_name, field_type, field_value, project_id, target):
    if field_type.startswith("user"):
        import_single_user(field_value, target)
        field_value = field_value.login
    if field_name in youtrack.EXISTING_FIELDS:
        return
    custom_field = target.getProjectCustomField(project_id, field_name)
    if hasattr(custom_field, "bundle"):
        bundle = target.getBundle(field_type, custom_field.bundle)
        target.addValueToBundle(bundle, field_value)


def get_yt_field_type(field_name, target):
    if field_name in bugzilla.FIELD_TYPES:
        return bugzilla.FIELD_TYPES[field_name]


def get_yt_field_name(field_name, target):
    if field_name in bugzilla.FIELD_NAMES:
        return bugzilla.FIELD_NAMES[field_name]
    if field_name in youtrack.EXISTING_FIELDS:
        return field_name
    try:
        target.getCustomField(field_name)
        return field_name
    except YouTrackException:
        return None


def to_yt_issue(bz_issue, project_id, target):
    issue = Issue()
    issue.comments = []
    for key, value in bz_issue:
        if key in ['flags', 'tags', 'attachments', 'comments']:
            continue
        field_name = get_yt_field_name(key, target)
        if field_name is None:
            continue
        if not len(value):
            continue
        if not isinstance(value, list):
            value = [value]
        field_type = get_yt_field_type(field_name, target)
        for v in value:
            add_value_to_field(field_name, v, field_type, project_id, target)
        if field_type.startswith("user"):
            value = [v.login for v in value]
        if field_type == "date":
            value = [to_unix_date(v) for v in value]
        issue[field_name] = value
    if "comments" in bz_issue:
        issue.comments = [to_yt_comment(comment, target) for comment in bz_issue["comments"]]
    return issue


def get_name_for_new_cf(cf):
    if cf in bugzilla.FIELD_NAMES:
        return bugzilla.FIELD_NAMES[cf]
    return cf


def create_yt_custom_field(cf, target):
    cf_name = get_name_for_new_cf(cf.name)
    cf_type = bugzilla.CF_TYPES[cf.type]
    if cf_name in bugzilla.FIELD_TYPES:
        cf_type = bugzilla.FIELD_TYPES[cf_name]
    create_custom_field(target, cf_type, cf_name, True)


def create_project_field(project_id, target, name):
    yt_cf_name = get_name_for_new_cf(name)
    field_type = get_yt_field_type(yt_cf_name, target)
    process_custom_field(target, project_id, field_type, yt_cf_name)
    cf = target.getProjectCustomField(project_id, yt_cf_name)
    return cf, field_type


def process_components(components, project_id, target):
    cf, field_type = create_project_field(project_id, target, "component")
    if hasattr(cf, "bundle"):
        bundle = target.getBundle(field_type, cf.bundle)
        for c in components:
            new_component = bundle.createElement(c.name)
            if isinstance(new_component, OwnedField):
                if c.initial_owner is not None:
                    import_single_user(c.initialowner, target)
                    new_component.owner = c.login
            target.addValueToBundle(bundle, new_component)

def process_versions(versions, project_id, target):
    cf, field_type = create_project_field(project_id, target, "version")
    if hasattr(cf, "bundle"):
        bundle = cf.bundle
        for v in versions:
            new_version = bundle.createElement(v.value)
            if isinstance(new_version, VersionField):
                new_version.released = True
                new_version.archived = False
            target.addValueToBundle(bundle, new_version)
#
#def process_milestones(milestones, project_id, target):
#    cf, field_type = create_project_field(project_id, target, "milestone")
#    if hasattr(cf, "bundle"):
#        bundle = cf.bundle
#        for m in milestones:
#            target.addValueToBundle(bundle, milestone)
#


def bugzilla2youtrack(target_url, target_login, target_pass, bz_db, bz_host, bz_port, bz_login, bz_pass,
                      bz_product_names):
    print "target_url       :   " + target_url
    print "target_login     :   " + target_login
    print "target_pass      :   " + target_pass
    print "bz_db            :   " + bz_db
    print "bz_host          :   " + bz_host
    print "bz_port          :   " + str(bz_port)
    print "bz_login         :   " + bz_login
    print "bz_pass          :   " + bz_pass

    # connecting to bz
    client = Client(bz_host, int(bz_port), bz_login, bz_pass, db_name=bz_db)

    if not len(bz_product_names):
        answer = raw_input("All projects will be imported. Are you sure? [y/n]")
        if answer.capitalize() != "Y":
            sys.exit()
        bz_product_names = client.get_product_names()

    print "bz_product_names :   " + repr(bz_product_names)

    # connecting to yt
    target = Connection(target_url, target_login, target_pass)

    print "Creating issue link types"
    link_types = client.get_issue_link_types()
    for link in link_types:
        print "Processing link type [ %s ]" % link.name
        try:
            target.createIssueLinkType(to_yt_issue_link_type(link))
        except YouTrackException:
            print "Can't create link type [ %s ] (maybe because it already exists)" % link.name
    print "Creating issue link types finished"

    print "Creating custom fields"
    custom_fields = client.get_custom_fields()
    for cf in custom_fields:
        create_yt_custom_field(cf, target)
    print "Creating custom fields finished"

    for key in bugzilla.FIELD_TYPES:
        if key not in youtrack.EXISTING_FIELDS:
            create_custom_field(target, bugzilla.FIELD_TYPES[key], key, True, bundle_policy="1")

    bz_product_ids = []

    for name in bz_product_names:
        product_id = client.get_product_id_by_name(name)
        bz_product_ids.append(product_id)
        print "Creating project [ %s ] with name [ %s ]" % (product_id, name)
        try:
            target.getProject(str(product_id))
        except YouTrackException:
            target.createProjectDetailed(str(product_id), name, client.get_project_description(product_id),
                target_login)

        print "Importing components for project [ %s ]" % product_id
        process_components(client.get_components(product_id), product_id, target)
        print "Importing components finished for project [ %s ]" % product_id

        print "Importing versions for project [ %s ]" % product_id
        process_versions(client.get_versions(product_id), product_id, target)
        print "Importing versions finished for project [ %s ] finished" % product_id

        print "Importing issues to project [ %s ]" % product_id
        max_count = 100
        count = 0
        bz_issues_count = client.get_issues_count(product_id)
        while count < bz_issues_count:
            batch = client.get_issues(product_id, count, max_count)
            count += max_count
            target.importIssues(product_id, product_id + " assignees",
                [to_yt_issue(bz_issue, product_id, target) for bz_issue in batch])
            # todo convert to good tags import
            for issue in batch:
                tags = issue["keywords"] | issue["flags"]
                for t in tags:
                    print "Processing tag [ %s ]" % t.encode('utf8')
                    target.executeCommand(str(product_id) + "-" + str(issue.id), "tag " + t.encode('utf8'))
            for issue in batch:
                for attach in issue["attachments"]:
                    print "Processing attachment [ %s ]" % (attach.name.encode('utf8'))
                    content = StringIO(attach.content)
                    target.createAttachment(str(product_id) + "-" + str(issue.id), attach.name, content, attach.reporter
                        , created=to_unix_date(attach.created))
        print "Importing issues to project [ %s ] finished" % product_id

    # todo add pagination to links
    print "Importing issue links"
    cf_links = client.get_issue_links()
    duplicate_links = client.get_duplicate_links()
    if len(duplicate_links):
        try:
            target.createIssueLinkTypeDetailed("Duplicate", "duplicates", "is duplicated by", True)
        except YouTrackException:
            print "Can't create link type [ Duplicate ] (maybe because it already exists)"
    depend_links = client.get_dependencies_link()
    if len(depend_links):
        try:
            target.createIssueLinkTypeDetailed("Depend", "depends on", "is required for", True)
        except YouTrackException:
            print "Can't create link type [ Depend ] (maybe because it already exists)"
    links = cf_links | duplicate_links | depend_links

    links_to_import = list([])
    for link in links:
        print "Processing link %s for issue%s" % (link.name, link.source)
        if (link.target_product_id in bz_product_ids) and (link.source_product_id in bz_product_ids):
            links_to_import.append(to_yt_issue_link(link))
    print target.importLinks(links_to_import)
    print "Importing issue links finished"

if __name__ == "__main__":
    main()
