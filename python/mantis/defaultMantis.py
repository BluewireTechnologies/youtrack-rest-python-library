import mantis

# maps the cf type in mantis with the cf type in yt
mantis.CF_TYPES = {
    0 : "string",     #String
    1 : "integer",    #Nimeric
    2 : "string",     #Float
    3 : "enum[1]",    #Enumeration
    4 : "string",     #Email
    5 : "enum[*]",    #Checkbox
    6 : "enum[1]",    #List
    7 : "enum[*]",    #Multiselection list
    8 : "date",       #Date
    9 : "enum[1]"     # Radio
}

# maps mantis priorities with yt priorities
PRIORITY = {
    "none"      : "Minor",
    "low"       : "Minor",
    "normal"    : "Normal",
    "high"      : "Major",
    "urgent"    : "Critical",
    "immediate" : "Show-stopper"
}
# maps the int value from mantis db with its human readable representation
TYPE = {
    "Feature"   :   "Feature",
    "Trivial"   :   "Bug",
    "Text"      :   "Bug",
    "Tweak"     :   "Bug",
    "Minor"     :   "Bug",
    "Major"     :   "Bug",
    "Crash"     :   "Bug",
    "Block"     :   "Bug"
}
# maps the int value from mantis db with its human readable representation
STATUS = {
    "confirmed" : "Verified"
}
# maps the int value from mantis db with its human readable representation
RESOLUTION = {
    "open" : "Open",
    "fixed" : "Fixed",
    "reopened" : "Reopened",
    "unable to reproduce" : "Can't Reproduce",
    "not fixable" : "Won't fix",
    "duplicate" : "Duplicate",
    "no change required" : "Obsolete",
    "suspended" : "Incomplete",
    "won't fix" : "Won't fix"
}

#maps mantis link types with yt link types
mantis.LINK_TYPES = {
    0 : "Duplicate",    #duplicate of
    1 : "Relates",      #related to
    2 : "Depend"        #parent of
}

mantis.FIELD_NAMES = {
    u"severity"         :   [u"Severity", u"Type"],
    u"handler"          :   [u"Assignee"],
    u"status"           :   [u"State"],
    u"resolution"       :   [u"State"],
    u"category"         :   [u"Subsystem"],
    u"version"          :   [u"Affected versions"],
    u"fixed_in_version" :   [u"Fix versions"], # DO NOT remove Fix versions form this list, if needed you can add one more field
                                                # but DO NOT delete Fix versions
    u"build"            :   [u"Fixed in build"],
    u"os_build"         :   [u"OS version"],
    u"subproject"       :   [u"Subproject"],
    u"os"               :   [u"OS"],
    u"due_date"         :   [u"Due date"],
    u"target_version"   :   [u"Target version"] # it's better to import this fields with version type
}

mantis.FIELD_VALUES = {
    u"State"     :   dict(RESOLUTION.items() + STATUS.items()),
    u"Priority"  :   PRIORITY,
    u"Type"      :   TYPE
}

mantis.FIELD_TYPES = {
    u"Priority"             :   "enum[1]",
    u"Type"                 :   "enum[1]",
    u"State"                :   "state[1]",
    u"Fix versions"         :   "version[*]",
    u"Affected versions"    :   "version[*]",
    u"Assignee"             :   "user[1]",
    u"Fixed in build"       :   "build[1]",
    u"Subsystem"            :   "ownedField[1]",
    u"Subproject"           :   "ownedField[1]",
    u"Severity"             :   "enum[1]",
    u"Platform"             :   "string",
    u"OS"                   :   "string",
    u"OS version"           :   "string",
    u"Reproducibility"      :   "enum[1]",
    u"Due date"             :   "date",
    u"Target version"       :   "version[1]"
}


# if this parameter is True custom field "Subproject" will be created,
# else all information about subproject will be lost
mantis.CREATE_CF_FOR_SUBPROJECT = True
# charset of your mantis database
mantis.CHARSET = "cp866"
  