from youtrack.connection import Connection
from bugzilla.bzClient import Client
from youtrack import *
from bugzilla import BzCustomField
from StringIO import StringIO
import bugzilla.defaultBzMapping
import bugzilla
import sys
import time

def main() :
#
#    target_url = "http://localhost:8081"
#    target_login = "root"
#    target_pass = "root"
#    bz_db = "bugs"
#    bz_host = "localhost"
#    bz_port = 3306
#    bz_login = "root"
#    bz_pass = "root"
#    bz_product_names = ["Botsman2", "BZProduct"]
    try :
        target_url, target_login, target_pass, bz_db, bz_host, bz_port, bz_login, bz_pass = sys.argv[1:9]
        bz_product_names = sys.argv[9:]
    except :
        sys.exit()
    bugzilla2youtrack(target_url, target_login, target_pass, bz_db, bz_host, bz_port, bz_login, bz_pass, bz_product_names)

def to_yt_user(bz_user) :
    user = User()
    user.login = bz_user.login
    user.email = bz_user.email
    user.fullName = bz_user.full_name
    return user

def to_yt_comment(bz_comment) :
    comment = Comment()
    if bz_comment.reporter != "":
        comment.author = bz_comment.reporter
    else :
        comment.author = "guest"
    if bz_comment.content != "":
        comment.text = bz_comment.content
    else :
        if not bugzilla.ACCEPT_EMPTY_COMMENTS:
            return None
        comment.text = "<no text>"
    comment.created = str(int(bz_comment.time * 1000))
    return comment

def to_yt_issue_link_type(bz_link_type) :
    link_type = IssueLinkType()
    link_type.name = bz_link_type.name
    if bz_link_type.description != "":
        link_type.outwardName = bz_link_type.description
        link_type.inwardName = "incoming " + bz_link_type.description
    else :
        link_type.outwardName = bz_link_type.name
        link_type.inwardName = "incoming " + bz_link_type.name
    link_type.directed = True
    return link_type

def to_yt_issue_link(bz_issue_link) :
    link = Link()
    link.typeName = bz_issue_link.name
    link.source = str(bz_issue_link.target_product_id) + "-" + str(bz_issue_link.target)
    link.target = str(bz_issue_link.source_product_id) + "-" + str(bz_issue_link.source)
    return link


def to_yt_subsystem(bz_component) :
    subsys = Subsystem()
    subsys.name = bz_component.name
    subsys.isDefault = False
    subsys.defaultAssignee = bz_component.initial_owner
    return subsys

def to_yt_version(bz_version) :
    version = Version()
    version.name = bz_version.value
    version.isReleased = True
    version.isArchived = False
    version.releaseDate = str(int(time.time() * 1000))
    return version

def to_yt_issue(bz_issue) :
    issue = Issue()
    issue.numberInProject = bz_issue.id
    issue.summary = bz_issue.summary
    issue.created = str(int(bz_issue.created * 1000))
    issue.reporterName = bz_issue.reporter
    if bz_issue.assignee != "":
        issue.assigneeName = bz_issue.assignee
    issue.subsystem = bz_issue.component
    issue.affectsVersion = bz_issue.version
    issue.voterName = bz_issue.voters
    # type
    if bz_issue.severity == "enhancement":
        issue.type = "Feature"
    else :
        issue.type = "Bug"
    # priority
    issue.priority = bugzilla.PRIORITY[bz_issue.priority]
    # state
    if bz_issue.status in bugzilla.STATUS:
        issue.state = bugzilla.STATUS[bz_issue.status]
    elif bz_issue.resolution in bugzilla.RESOLUTION:
        issue['Resolution'] = bugzilla.RESOLUTION[bz_issue.resolution]
        issue.state = "Fixed"
    # comments
    issue.comments = []
    first = True
    for c in bz_issue.comments :
        if first:
            issue.description = c.content
            first = False
        else :
            yt_comment = to_yt_comment(c)
            if yt_comment is not None:
                issue.comments.append(yt_comment)
#    if (len(bz_issue.cc) > 0) :
#        issue.watcherName = bz_issue.cc
    # custom fields
    for key in bz_issue.cf :
        issue[key] = bz_issue.cf[key]
    issue["OS"] = bz_issue.op_sys
    issue["Platform"] = bz_issue.platform
    
    return issue


def bugzilla2youtrack(target_url, target_login, target_pass, bz_db, bz_host, bz_port, bz_login, bz_pass, bz_product_names) :
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

    # not related with exact project
    print "Importing users"
    # getting users
    users = client.get_bz_users()
    # converting users
    yt_users = list([])
    for user in users :
        print "Processing user [ %s ]" % user.login
        yt_users.append(to_yt_user(user))
    # importing users
    target.importUsers(yt_users)
    print "Importing users finished"


    print "Creating issue link types"
    link_types = client.get_issue_link_types()
    for link in link_types :
        print "Processing link type [ %s ]" % link.name
        try :
            target.createIssueLinkType(to_yt_issue_link_type(link))
        except YouTrackException:
            print "Can't create link type [ %s ] (maybe because it already exists)" % link.name
    print "Creating issue link types finished"


    print "Creating custom fields"
    #getting custom field definitions
    custom_fields = client.get_custom_fields()

#    #we should check whether there is a Type field
#    yt_custom_fields = target.getCustomFields()
#    contains_type = False
#    for cf in yt_custom_fields :
#        if (cf.name == "Type") :
#            contains_type = True
#            break
#    if not (contains_type) :
#        type_cf = BzCustomField("Type")
#        type_cf.values = ["Bug", "Feature"]
#        type_cf.type = "2"      # single select
#        custom_fields.append(type_cf)

    # creating cf for OS (it is default field in bz)
    op_systems = client.get_op_systems()
    if len(op_systems):
        os_cf = BzCustomField("OS")
        os_cf.values = op_systems
        os_cf.type = "2"        #single select
        custom_fields.append(os_cf)

    # creating cf for platform (it is a default field in bz)
    platforms = client.get_platforms()
    if len(platforms):
        platform_cf = BzCustomField("Platform")
        platform_cf.values = platforms
        platform_cf.type = "2"  #single select
        custom_fields.append(platform_cf)

    for cf in custom_fields :
        print "Processing custom field [ %s ]" % cf.name
        cf_type = bugzilla.CF_TYPES[cf.type]
        if cf_type in ["enum[1]", "enum[*]"]:
            bundle_name= cf.name + "_enum"
            try :
                print "Creating enum bundle with name [ %s ]" % bundle_name
                target.createEnumBundleDetailed(bundle_name, cf.values)
            except YouTrackException:
                print "Can't create enum with name [ %s ] (maybe because it already exists)" % bundle_name
        try :
            target.createCustomFieldDetailed(cf.name, cf_type, False, True)
        except YouTrackException:
            print "Can't create prototype for custom field [ %s ] (maybe because it already exists)" % cf.name
    print "Creating custom fields finished"

    bz_product_ids = []


    for name in bz_product_names :
        product_id = client.get_product_id_by_name(name)
        bz_product_ids.append(product_id)
        print "Creating project [ %s ] with name [ %s ]" % (product_id, name)
        try :
            target.getProject(str(product_id))
        except YouTrackException:
            target.createProjectDetailed(str(product_id), name, client.get_project_description(product_id), target_login)

        print "Importing components for project [ %s ]" % product_id
        components = client.get_components(product_id)
        # we convert component into subsystem
        for cmp in components :
            print "Processing subsystem [ %s ]" % cmp.name
            try :
                target.createSubsystem(str(product_id), to_yt_subsystem(cmp))
            except YouTrackException:
                print "Can't create subsystem [ %s ] in project [ %s ] (maybe because it already exists)" % (cmp.name, product_id)
        print "Importing components finished for project [ %s ]" % product_id

        print "Importing versions for project [ %s ]" % product_id
        versions = client.get_versions(product_id)
        for vers in versions :
            print "Processing version [ %s ]" % vers.value
            try :
                target.createVersion(str(product_id), to_yt_version(vers))
            except YouTrackException:
                print "Can't create subsystem [ %s ] in project [ %s ] (maybe because it already exists)" % (vers.name, product_id)
        print "Importing versions finished for project [ %s ] finished" % product_id

        print "Attaching custom fields to project [ %s ]" % product_id
        for cf in custom_fields :
            try :
                target.createProjectCustomFieldDetailed(str(product_id), cf.name, "No " + cf.name, params={'bundle': cf.name + "_enum"})
            except YouTrackException:
                print "Can't attach custom field [ %s ] to project [ %s ] (maybe because if was already attached)" % (cf.name, product_id)
        print "Attaching custom fields to project [ %s ] finished" % product_id

        print "Importing issues to project [ %s ]" % product_id
        max_count = 100
        count = 0
        issues = client.get_issues(product_id)
        yt_issues = list([])
        for i in issues :
            yt_issues.append(to_yt_issue(i))
            count += 1
            if count == max_count:
                target.importIssues(str(product_id), name + "Assignees", yt_issues)
                count = 0
                yt_issues = list([])
        print target.importIssues(str(product_id), name + "Assignees", yt_issues)
        print "Importig issues to project [ %s ] finished" % product_id

        print "Importing tags to issues from project [ %s ]" % product_id
        for issue in issues :
            print "Processing tags for issue [ %s ]" % (str(issue.id))
            tags = issue.keywords | issue.flags
            for t in tags :
                print "Processing tag [ %s ]" % t.encode('utf8')
                target.executeCommand(str(product_id) + "-" + str(issue.id), "tag " + t.encode('utf8'))
        print "Importing tags to issues from project [ %s ] finished" % product_id

        print "Importing attachments to project [ %s ]" % product_id
        for issue in issues :
            print "Processing attachments for issue [ %s ]" % (str(issue.id))
            for attach in issue.attachments :
                print "Processing attachment [ %s ]" % (attach.name.encode('utf8'))
                content = StringIO(attach.content)
                #content = open("/home/user/Desktop/Screenshot.png")
                target.createAttachment(str(product_id) + "-" + str(issue.id), attach.name, content, attach.reporter, created = str(int(attach.created * 1000)))
        print "Importing attachments to project [ %s ] finished" % product_id


    print "Importing issue links"
    cf_links = client.get_issue_links()
    duplicate_links = client.get_duplicate_links()
    if len(duplicate_links):
        try :
            target.createIssueLinkTypeDetailed("Duplicate", "duplicates", "is duplicated by", True)
        except YouTrackException:
            print "Can't create link type [ Duplicate ] (maybe because it already exists)"
    depend_links = client.get_dependencies_link()
    if len(depend_links):
        try :
            target.createIssueLinkTypeDetailed("Depend", "depends on", "is required for", True)
        except YouTrackException:
            print "Can't create link type [ Depend ] (maybe because it already exists)"
    links = cf_links | duplicate_links | depend_links

    links_to_import = list([])
    for link in links :
        print "Processing link %s for issue%s" % (link.name, link.source)
        if (link.target_product_id in bz_product_ids) and (link.source_product_id in bz_product_ids):
            links_to_import.append(to_yt_issue_link(link))
    print target.importLinks(links_to_import)
    print "Importing issue links finished"

if __name__ == "__main__":
    main()
