import bugzilla

bugzilla.STATUS = {
    "UNCONFIRMED"   :   "Open",
    "NEW"           :   "Submitted",
    "ASSIGNED"      :   "Submitted",
    "REOPENED"      :   "reopened"
}

bugzilla.RESOLUTION = {
    "FIXED"         :   "Fixed",
    "INVALID"       :   "Can't Reproduce",
    "WONTFIX"       :   "Won't fix",
    "DUPLICATE"     :   "Duplicate",
    "WORKSFORME"    :   "Can't Reproduce",
    "MOVED"         :   "Won't fix",
    "LATER"         :   "Won't fix",
}

# mapping between cf types in bz and youtrack
bugzilla.CF_TYPES = {
    "1"             :   "string",   #FIELD_TYPE_FREETEXT
    "2"             :   "enum[1]",  #FIELD_TYPE_SINGLE_SELECT
    "3"             :   "enum[*]",  #FIELD_TYPE_MULTY_SELECT
    "4"             :   "string",   #FIELD_TYPE_TEXTAREA
    "5"             :   "string",   #FIELD_TYPE_DATETIME
    "7"             :   "string"    #FIELD_TYPE_BUG_URLS
}


bugzilla.PRIORITY = {
    #bz priority         yt priority
    "Lowest"        :   "4",        #Minor
    "Low"           :   "3",        #Normal
    "Normal"        :   "2",        #Major
    "High"          :   "1",        #Critical
    "Highest"       :   "0",        #Show-stopper
    "---"           :   "3"         #Normal
}

# if we need to import empty comments
bugzilla.ACCEPT_EMPTY_COMMENTS = False
bugzilla.BZ_DB_CHARSET = 'cp866'