import fbugz

fbugz.CF_NAMES = {
    u'assignee'          :   u'Assignee',
    u'area'              :   u'Subsystem',
    u'category'          :   u'Type',
    u'fix_for'           :   u'Fix versions',
    u'priority'          :   u'Priority',
    u'status'            :   u'State',
    u'due'               :   u'Due date',
    u'original_title'    :   u'Original title',
    u'version'           :   u'Version',
    u'computer'          :   u'Computer',
    u'estimate'          :   u'Estimate'
}

fbugz.CF_TYPES = {
    u'Assignee'          :   'user[1]',
    u'Subsystem'         :   'ownedField[1]',
    u'Fix versions'      :   'version[*]',
    u'Priority'          :   'enum[1]',
    u'State'             :   'state[1]',
    u'Due date'          :   'date',
    u'Original title'    :   'string',
    u'Version'           :   'string',
    u'Computer'          :   'string',
    u'Estimate'          :   'integer',
    u'Type'              :   'enum[1]'
}

fbugz.PROJECTS_TO_IMPORT = ["Sample_Project"]
