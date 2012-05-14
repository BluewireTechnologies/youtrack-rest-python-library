# mapping for default google code project
import googleCode

print "Use youtrack-android mapping scheme"

googleCode.STATES = {'Submitted': 'Submitted',
                     'InProgress': 'In Progress',
                     'Fixed': 'Fixed',
                     'Duplicate': 'Duplicate',
                     'WontFix': 'Won\'t fix',
                     'Accepted': 'Open'}

googleCode.TYPES = {'Type-Defect': 'Bug',
                    'Type-Feature': 'Feature',
                    'Type-Task': 'Task',
                    'Type-Enhancement': 'Usability Problem'}

googleCode.PRIORITIES = {'Priority-Minor': '0',
                         'Priority-Normal': '3',
                         'Priority-Medium': '3',
                         'Priority-Major': '2',
                         'Priority-Critical': '1'}

googleCode.FIELD_TYPES = {
    "State": "state[1]",
    "Priority": "enum[1]",
    "Type": "enum[1]",
    "Assignee": "user[1]"
}



#googleCode.CUSTOM_FIELDS = {
#            'OS'        : {'name': 'testOS', 'type' : 'enum[*]', 'isPrivate': False, 'defaultVisibility': True, 'empty' : 'No OS'},
#            'Browser'   : {'name': 'testBrowser', 'type' : 'enum[*]', 'isPrivate': False, 'defaultVisibility': True, 'empty' : 'No Bro'}}
