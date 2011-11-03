# mapping for default google code project
import googleCode

print "Use default mapping scheme"

googleCode.STATES = {'Submitted'  : 'Submitted',
          'InProgress' : 'In Progress',
          'Fixed'      : 'Fixed',
          'Duplicate'  : 'Duplicate',
          'WontFix'    : 'Won\'t fix',
          'Accepted'   : 'Open'}

googleCode.TYPES = {'Type-Defect'      : 'Bug',
         'Type-Feature'     : 'Feature',
         'Type-Task'        : 'Task',
         'Type-Enhancement' : 'Usability Problem'}

googleCode.PRIORITIES = {'Priority-Minor'    : '0',
              'Priority-Normal'   : '3',
              'Priority-Medium'   : '3',
              'Priority-Major'    : '2',
              'Priority-Critical' : '1'}
