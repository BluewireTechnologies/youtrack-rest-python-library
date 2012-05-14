import googleCode

googleCode.FIELD_NAMES = {
    "owner"     : "Assignee",
    "status"    : "State",
    "Milestone" : "Fix versions"
}

googleCode.FIELD_TYPES = {"State" : "state[1]",
                          "Priority" : "enum[1]",
                          "Type" : "enum[1]",
                          "Assignee" : "user[1]",
                          "Fix versions" : "version[*]",
                          "Module" : "ownedField[1]"
}
