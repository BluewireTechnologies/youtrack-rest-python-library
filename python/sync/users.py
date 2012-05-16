import youtrack

PROHIBITED = '/'

class UserImporter(object):
    def __init__(self, source, target, caching_users=True):
        self.source = source
        self.target = target
        self.caching_users = caching_users
        self.created_user_logins = set([user.login for user in target.getUsers()]) if caching_users else set([])
        self.created_group_names = set([group.name for group in target.getGroups()])
        self.created_role_names = set([role.name for role in target.getRoles()])
        self.created_project_ids = set(target.getProjectIds())

    def addCreatedProjects(self, project_ids):
        self.created_project_ids |= set(project_ids)

    def resetConnections(self, source, target):
        self.source = source
        self.target = target

    def importUser(self, user):
        filtered_user = self._filter_user(user)
        if filtered_user:
            self.target.importUsers([filtered_user])

    def importUsersRecursively(self, users):
        total_users = len(users)
        if not total_users: return
        user_list = list(users)
        max_users = 100
        start = 0
        imported_size = 0
        while start < total_users:
            user_batch = user_list[start:start + max_users]
            imported_size += self._import_user_batch_recursively(user_batch)
            start += max_users
        return imported_size

    def _import_groups_of(self, yt_user):
        user_groups = self.source.getUserGroups(yt_user.login)
        for group in user_groups:
            if group.name not in self.created_group_names:
                try:
                    self.createGroup(group)
                except Exception, ex:
                    print repr(ex).encode('utf-8')
            self.target.setUserGroup(yt_user.login, group.name)
            print "Set " + str(yt_user.login) + " to " + str(group.name)

    def _import_user_batch_recursively(self, users):
        if not len(users): return 0
        users_to_import = []
        for user in users:
            filtered_user = self._filter_user(user)
            if filtered_user: users_to_import.append(filtered_user)
        print self.target.importUsers(users_to_import)
        for yt_user in users_to_import:
            self._import_groups_of(yt_user)
            if self.caching_users: self.created_user_logins.add(yt_user.login)
        return len(users_to_import)

    def _filter_user(self, user):
        if (not self.caching_users or user.login not in self.created_user_logins) and self._check_login(user.login):
            if not hasattr(user, "email"):
                user.email = "<no email>"
            return user
        return None

    def importGroupsWithoutUsers(self, groups):
        if not len(groups): return
        for group in groups:
            if group.name not in self.created_group_names:
                try:
                    self.createGroup(group)
                except Exception, ex:
                    print repr(ex).encode('utf-8')

    def createGroup(self, group):
        group_roles = self.source.getGroupRoles(group.name)
        self.target.createGroup(group)
        self.created_group_names.add(group.name)
        for user_role in group_roles:
            role = self.source.getRole(user_role.name)
            if role.name not in self.created_role_names:
                self._create_role(role)
            self._add_user_role_to_group_safely(group, user_role)


    def _add_user_role_to_group_safely(self, group, user_role):
        restricted_user_role = youtrack.UserRole()
        restricted_user_role.name = user_role.name
        for project in user_role.projects:
            if project in self.created_project_ids:
                restricted_user_role.projects.append(project)
        self.target.addUserRoleToGroup(group, restricted_user_role)

    def _create_role(self, role):
        permissions = self.source.getRolePermissions(role)
        self.target.createRole(role)
        self.created_role_names.add(role.name)
        for prm in permissions:
            self.target.addPermissionToRole(role, prm)

    def _check_login(self, login):
        failed = 1 in [c in login for c in PROHIBITED]
        if failed: print "Could not import user [" + login + "], login contains prohibited chars: " + PROHIBITED
        return not failed
