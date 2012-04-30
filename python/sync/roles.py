
def import_distinct_roles(source, target):
    source_group_names = set([group.name for group in source.getGroups()])
    required_target_group_names = [group.name for group in target.getGroups() if group.name in source_group_names]

    required_for_import_role_names = set([])
    for name in required_target_group_names:
        required_for_import_role_names |= set([ur.name for ur in source.getGroupRoles(name)])

    roles = source.getRoles()
    slave_role_names = set([role.name for role in target.getRoles()])
    for role in roles:
        if role.name not in slave_role_names:
            if role.name in required_for_import_role_names:
                target.createRole(role)
                permissions = source.getRolePermissions(role)
                for permission in permissions:
                    target.addPermissionToRole(role, permission)
