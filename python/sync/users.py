class UserImporter(object):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.created_user_logins = set([user.login for user in target.getUsers()])
        self.created_group_names = set([group.name for group in target.getGroups()])
        self.created_role_names = set([role.name for role in target.getRoles()])

    def resetConnections(self, source, target):
        self.source = source
        self.target = target

    def importUsers(self, users):
        if not len(users): return
        new_users = [user for user in users if user.login not in self.created_user_logins]
        if not len(new_users): return
        print "Create users [" + str(len(new_users)) + "]"
        for user in new_users:
            if not hasattr(user, "email"): user.email = "<no email>"
        print self.target.importUsers(new_users)
        for yt_user in new_users:
            user_groups = self.source.getUserGroups(yt_user.login)
            for group in user_groups:
                if group.name not in self.created_group_names:
                    try:
                        self._createGroup(group)
                    except Exception, ex:
                        print repr(ex).encode('utf-8')
                try:
                    self.target.setUserGroup(yt_user.login, group.name)
                except:
                    pass
            self.created_user_logins.add(yt_user.login)

    def _createGroup(self, group):
        group_roles = self.source.getGroupRoles(group.name)
        self.target.createGroup(group)
        self.created_group_names.add(group.name)
        for gr in group_roles:
            role = self.source.getRole(gr.name)
            if role.name not in self.created_role_names:
                self._createRole(role)
            self.target.addUserRoleToGroup(group, gr)

    def _createRole(self, role):
        permissions = self.source.getRolePermissions(role)
        self.target.createRole(role)
        self.created_role_names.add(role.name)
        for prm in permissions:
            self.target.addPermissionToRole(role, prm)
