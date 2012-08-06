import tracLib

#if you defined your own types you should add them to the map
TYPES = {
    "defect"        :   "Bug",
    "feature request"   :   "Feature",
    "task"          :   "Task",
    "usability issue" : "Usability Problem",
    "technical debt" : "Technical Debt"
}

#if you defined your own priorities you should add them to the map
PRIORITIES = {
    "low"       :   "Minor",        #Minor
    "medium"         :   "Normal",        #Normal
    "high"         :   "Major",        #Major
}
#we convert resolutions and statuses into statuses
RESOLUTIONS = {
    "duplicate"     :   "Duplicate",
    "fixed"         :   "Fixed",
    "wontfix"       :   "Won't fix",
    "worksforme"    :   "Can't Reproduce",
    "invalid"       :   "Won't fix"
    #   :   "To be discussed
}
STATES = {
    "accepted"      :   "Submitted",
    "new"           :   "Open",
    "reopened"      :   "Reopened",
    "assigned"      :   "Submitted",
    "closed"        :   None,
    "test"          :   "Test",
    "blocked"       :   "Blocked"
}

# if you don't change rules of importing, don't change this map
tracLib.CUSTOM_FIELD_TYPES = {
    "text"          :   "string",
    "checkbox"      :   "enum[*]",
    "select"        :   "enum[1]",
    "radio"         :   "enum[1]",
    "textarea"     :   "string"
}

tracLib.FIELD_VALUES = {
    "Priority"      :   PRIORITIES,
    "Type"          :   TYPES,
    "State"         :   dict(RESOLUTIONS.items() + STATES.items()),
}

tracLib.FIELD_TYPES = {
    "Priority"          :   "enum[1]",
    "Type"              :   "enum[1]",
    "State"             :   "state[1]",
    "Fix versions"      :   "version[*]",
    "Affected versions" :   "version[*]",
    "Assignee"          :   "user[1]",
    "Severity"          :   "enum[1]",
    "Subsystem"         :   "ownedField[1]"
}

tracLib.FIELD_NAMES = {
    "Resolution"        :   "State",
    "Status"            :   "State",
    "Owner"             :   "Assignee",
    "Component"         :   "Subsystem",
    "Milestone"         :   "Fix versions",
}

# the default email to register users who doesn't have one
tracLib.DEFAULT_EMAIL = "unknown@bluewire-technologies.com"
# if true users who were not authorized are registered
# else they are known as guests
tracLib.ACCEPT_NON_AUTHORISED_USERS = True