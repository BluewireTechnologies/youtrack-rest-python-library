# mapping for chromium google code project
import googleCode

print "Use chromium mapping scheme"
#
#googleCode.STATES = {
#          'Assigned'            : 'Open',
#          'Available'           : 'Fixed',
#          'Fixed'               : 'Fixed',
#          'ExternalDependency'  : 'Open',
#          'Started'             : 'In Progress',
#          'Uptriaged'           : 'Open',
#          'Upstream'            : 'Open'}
#
#googleCode.TYPES = {'Type-Bug'      : 'Bug',
#         'Type-Feature'     : 'Feature',
#         'Type-Task'        : 'Task',
#         'Type-Enhancement' : 'Usability Problem'}
#
#googleCode.PRIORITIES = {
#              'Pri-0'   : '3',
#              'Pri-1'   : '2',
#              'Pri-2'   : '1'}

googleCode.FIELD_NAMES = {
    "owner" : "Assignee",
    "status" : "State",
    "Mstone" : "Fix versions",
    "Sev" : "Severity"
}


googleCode.FIELD_TYPES = {"State" : "state[1]",
                          "Priority" : "enum[1]",
                          "Type" : "enum[1]",
                          "Area" : "ownedField[*]",
                          "Feature" : "enum[*]",
                          "OS" : "enum[*]",
                          "Size" : "enum[*]",
                          "Assignee" : "user[1]",
                          "Fix versions" : "version[*]",
                          "Pri" : "enum[*]",
                          "ReleaseBlock" : "version[*]",
                          "Stability" : "enum[1]",
                          "merge" : "string",
                          "Iteration" : "version[*]",
                          "Hotlist" : "enum[1]",
                          "Team" : "ownedField[1]",
                          "Action" : "enum[1]",
                          "Severity" : "enum[1]"
}
#
#
#googleCode.CUSTOM_FIELDS = {
#            'Area'      : {'name': 'Area', 'type' : 'enum[*]', 'isPrivate': False, 'defaultVisibility': True, 'empty' : 'No Area'},
#            'Feature'   : {'name': 'Feature', 'type' : 'enum[*]', 'isPrivate': False, 'defaultVisibility': True, 'empty' : 'No Feature'},
#            'OS'        : {'name': 'OS', 'type' : 'enum[*]', 'isPrivate': False, 'defaultVisibility': True, 'empty' : 'No OS'},
#            'Size'      : {'name': 'Size', 'type' : 'enum[*]', 'isPrivate': False, 'defaultVisibility': True, 'empty' : 'No Size'}}