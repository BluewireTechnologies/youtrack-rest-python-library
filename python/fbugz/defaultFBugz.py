# -*- coding: utf-8 -*-
import fbugz

fbugz.PROJECTS_TO_IMPORT = [u'Hello']

fbugz.CF_NAMES = {
    'ix_bug'            :   'numberInProject',
    'title'             :   'summary',
    'opened'            :   'created',
    'reporter'          :   'reporter',
    'assignee'          :   'Assignee',
    'area'              :   'Subsystem',
    'category'          :   'Type',
    'fix_for'           :   'Fix versions',
    'priority'          :   'Priority',
    'status'            :   'State',
    'due'               :   'Due date',
    'original_title'    :   'Original title',
    'version'           :   'Version',
    'computer'          :   'Computer',
    'estimate'          :   'Estimate'
}

fbugz.CF_TYPES = {
    'Assignee'          :   'user[1]',
    'Subsystem'         :   'ownedField[1]',
    'Fix versions'      :   'version[*]',
    'Priority'          :   'enum[1]',
    'State'             :   'state[1]',
    'Due date'          :   'date',
    'Original title'    :   'string',
    'Version'           :   'string',
    'Computer'          :   'string',
    'Estimate'          :   'int'
}

CATEGORY = {
    'Feature'       :   'Feature',
    'Bug'           :   'Bug',
    'Inquiry'       :   'Feature',
    'Schedule Item' :   'Task'
}

PRIORITY = {
    1   :   'Show-stopper',
    2   :   'Critical',
    3   :   'Critical',
    4   :   'Major',
    5   :   'Normal',
    6   :   'Normal',
    7   :   'Minor'
}

STATUS = {
    "Active"            :   "Open",
    "Fixed"             :   "Fixed",
    "Implemented"       :   "Fixed",
    "Responded"         :   "Fixed",
    "Completed"         :   "Fixed",
    "Not Reproducible"  :   "Can't reproduce",
    "Duplicate"         :   "Duplicate",
    "Already Exists"    :   "Duplicate",
    "Postponed"         :   "Submitted",
    "Won't Fix"         :   "Won't Fix",
    "By Design"         :   "Won't Fix",
    "Won't Implement"   :   "Won't Fix",
    "Won't Respond"     :   "Won't Fix",
    "SPAM"              :   "Won't Fix",
    "Canceled"          :   "Won't fix",
    "Waiting For Info"  :   "Incomplete"
}

fbugz.CF_VALUES = {
    'Type'      :   CATEGORY,
    'Priority'  :   PRIORITY,
    'State'     :   STATUS
}



