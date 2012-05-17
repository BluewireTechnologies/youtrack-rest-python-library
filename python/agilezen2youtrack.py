import calendar
from xml.dom import minidom
import datetime
from agilezen.client import Client
from youtrack import YouTrackException, Link, User, Group, StateField, Issue, EnumBundle, StateBundle, Comment
from youtrack.connection import Connection

def main():
    source_url = "https://agilezen.com"
    source_token = "f68fb10868d1425787e5013c90fe33d0"
    target_url = "http://localhost:8081"
    target_login = "root"
    target_password = "root"
    agilezen2youtrack(source_url, source_token, target_url, target_login, target_password)


def to_yt_user(user):
    u = User()
    u.login = user[u'userName']
    u.email = user[u'email']
    if u'name' in user:
        u.fullName = user[u'name']
    return u


def import_user(target, user):
    target.importUsers([to_yt_user(user)])


def import_role(target, project_id, role):
    if u'members' not in role:
        return
    users_to_import = []
    members = role[u'members']
    for member in members:
        users_to_import.append(to_yt_user(member))
    target.importUsers(users_to_import)
    group = Group()
    group.name = project_id + "-" + role[u'name']
    try:
        target.createGroup(group)
    except YouTrackException, e:
        print unicode(e)
    for member in members:
        try:
            target.setUserGroup(member[u'userName'], group.name)
        except YouTrackException, e:
            print str(e)


def import_phase(target, project_id, phase):
    bundle = target.getBundle("state[1]", target.getProjectCustomField(project_id, "Phase").bundle)
    value = StateField()
    value.name = phase[u'name']
    value.description = phase[u'description']
    try:
        target.addValueToBundle(bundle, value)
    except YouTrackException, e:
        print unicode(e)


def add_value_to_custom_field(target, project_id, field_name, field_value):
    field_type = target.getCustomField(field_name).type
    bundle = target.getBundle(field_type, target.getProjectCustomField(project_id, field_name).bundle)
    try:
        target.addValueToBundle(bundle, field_value)
    except YouTrackException:
        pass

def get_created_date_for_story(story):
    return str(to_unix_date(story[u'metrics'][u'createTime']))

def to_yt_issue(target, project_id, story):
    parent = Issue()
    parent.numberInProject = str(story[u'id'])
    parent.summary = story[u'text']
    parent['Size'] = story[u'size']
    parent.created = get_created_date_for_story(story)
    color = story[u'color']
    add_value_to_custom_field(target, project_id, 'Color', color)
    parent['Color'] = color
    priority = story[u'priority']
    add_value_to_custom_field(target, project_id, 'Priority', priority)
    parent['Priority'] = priority
    parent['Deadline'] = str(to_unix_date(story[u'deadline']))
    status = story[u'status']
    add_value_to_custom_field(target, project_id, 'Status', status)
    parent['Status'] = status
    parent['Phase'] = story[u'phase'][u'name']
    creator = story[u'creator']
    import_user(target, creator)
    owner = story[u'owner']
    import_user(target, owner)
    parent.reporterName = creator[u'userName']
    parent['Assignee'] = owner[u'userName']
    parent.comments = []
    if u'comments' in story:
        for comment in story[u'comments']:
            parent.comments.append(to_yt_comment(target, comment))
    if u'details' in story:
        parent.description = story[u'details']
    return parent


def to_yt_sub_task(target, project_id, story, task):
    issue = Issue()
    issue.summary = task[u'text']
    issue.reporterName = story[u'creator'][u'userName']
    issue.created = str(to_unix_date(task[u'createTime']))
    if u'finishTime' in task:
        issue.resolved = task[u'finishTime']
    status = task[u'status']
    add_value_to_custom_field(target, project_id, "Status", status)
    issue['Status'] = status
    if u'finishedBy' in task:
        finished_by = task[u'finishedBy']
        import_user(target, finished_by)
        issue['Assignee'] = finished_by[u'userName']
    issue.comments = []
    return issue

#def to_yt_issue(target, project_id, task):
#    pass

def to_yt_comment(target, comment):
    c = Comment()
    author = comment[u'author']
    import_user(target, author)
    c.text = comment[u'text']
    c.author = author[u'userName']
    c.created = str(to_unix_date(comment[u'createTime']))
    return c


def to_unix_date(time):
    dt = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
    return calendar.timegm(dt.timetuple()) * 1000


def import_project(source, target, project):
    import_user(target, project[u'owner'])
    project_id = str(project[u'id'])
    try:
        target.getProject(project_id)
    except YouTrackException, e:
        target.createProjectDetailed(project_id, project[u'name'],
            project[u'description'], project[u'owner'][u'userName'])

    last_page = False
    current_page = 1
    while not last_page:
        roles = source.get_project_roles(project_id, current_page)
        if current_page == roles[u'totalPages']:
            last_page = True
        for role in roles[u'items']:
            import_role(target, project_id, role)
        current_page += 1
    last_page = False
    current_page = 1
    while not last_page:
        phases = source.get_project_phases(project_id, current_page)
        if current_page == phases[u'totalPages']:
            last_page = True
        for phase in phases[u'items']:
            import_phase(target, project_id, phase)
        current_page += 1
    last_page = False
    current_page = 1
    max_story_id = 0
    while not last_page:
        stories = source.get_stories_for_project(project_id, current_page)
        if current_page == stories[u'totalPages']:
            last_page = True
        stories_to_import = []
        items = stories[u'items']
        for story in items:
            story_id_ = story[u'id']
            story = to_yt_issue(target, project_id, story)
            if story_id_ > max_story_id:
                max_story_id = story_id_
            stories_to_import.append(story)
        target.importIssues(project_id, project_id + " assignees", stories_to_import)
        for story in items:
            if u'tags' in story:
                for tag in [t[u'name'] for t in story[u'tags']]:
                    target.executeCommand("%s-%s" % (project_id, story[u'id']), "tag " + tag)
        current_page += 1

    #now iterate again through stories to import tasks
    last_page = False
    current_page = 1
    while not last_page:
        stories = source.get_stories_for_project(project_id, current_page)
        if current_page == stories[u'totalPages']:
            last_page = True
        for story in stories[u'items']:
            tasks = [to_yt_sub_task(target, project_id, story, task) for task in
                     story['tasks']] if u'tasks' in story else []
            if len(tasks):
                for task in tasks:
                    max_story_id += 1
                    task.numberInProject = str(max_story_id)
                result = target.importIssues(project_id, project_id + " assignees", tasks)
                items = minidom.parseString(result).getElementsByTagName("item")
                issue_links_to_import = []
                for item in items:
                    link = Link()
                    link.typeName = "Subtask"
                    link.target = "%s-%s" % (project_id, item.attributes['id'].value)
                    link.source = "%s-%d" % (project_id, story[u'id'])
                    issue_links_to_import.append(link)
                target.importLinks(issue_links_to_import)
        current_page += 1


#        for parent_id, tasks in tasks_to_import:
#            import_result = target.importIssues(project_id, project_id + " assignees", tasks)
#


def agilezen2youtrack(source_url, source_token, target_url, target_login, target_password):
    source = Client(source_url, source_token)
    target = Connection(target_url, target_login, target_password)
    last_page = False
    current_page = 1
    try:
        target.createCustomFieldDetailed("Phase", "state[1]", False, True, True, {"attachBundlePolicy": "2"})
    except YouTrackException, e:
        print str(e)
    colors_bundle = EnumBundle()
    colors_bundle.name = "Colors"
    try:
        target.createBundle(colors_bundle)
    except YouTrackException, e:
        print str(e)
    try:
        target.createCustomFieldDetailed("Color", "enum[1]", False, True, True,
                {"defaultBundle": colors_bundle.name, "attachBundlePolicy": "0"})
    except YouTrackException, e:
        print str(e)
    try:
        status_bundle = StateBundle()
        status_bundle.name = "Statuses"
        target.createBundle(status_bundle)
        target.createCustomFieldDetailed("Status", "state[1]", False, True, True,
                {"defaultBundle": status_bundle.name, "attachBundlePolicy": "0"})
    except YouTrackException, e:
        print str(e)
    try:
        target.createCustomFieldDetailed("Size", "integer", False, True, True)
    except YouTrackException, e:
        print str(e)
    try:
        target.createCustomFieldDetailed("Deadline", "date", False, True, True)
    except YouTrackException, e:
        print str(e)
    while not last_page:
        projects = source.get_projects(page=1, page_size=25)
        if current_page == projects[u'totalPages']:
            last_page = True
        for project in projects[u'items']:
            import_project(source, target, project)
        current_page += 1


if __name__ == '__main__':
    main()