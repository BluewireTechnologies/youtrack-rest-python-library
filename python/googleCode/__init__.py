STATES = None
DEFAULT_UNRESOLVED_STATUS = 'Submitted'
DEFAULT_RESOLVED_STATUS = 'Fixed'
TYPES = None
PRIORITIES = None

FIELD_NAMES = {}
FIELD_TYPES = {}
EXISTING_FIELDS = ['numberInProject', 'projectShortName', 'summary', 'description', 'created',
                   'updated', 'updaterName', 'resolved', 'reporterName']

# custom fields to create for imported labels
# {'labelPrefix': {'name':'name', type':'enum[*]', isPrivate:False, defaultVisibility:True}}
# supported types are: enum[*], enum[1], date, integer, string
CUSTOM_FIELDS = {}
