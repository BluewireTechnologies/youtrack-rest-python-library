import csvClient
from time import time

csvClient.IGNORE_COLUMNS = ["Due Date", "Votes", "Images", "Original Estimate", "Remaining Estimate",
                            "Time Spent", "Work Ratio", "Security Level", "Progress", "? Progress",
                            "? Time Spent", "? Remaining Estimate", "? Original Estimate", "Mantis ID",
                            "Patch Submitted", "Participants", "Testcase included", "Bugzilla Id",
                            "Patch attached", "Days since last comment", "Number of attachments",
                            "Source ID", "Project", "Status"]

# maps issue fields with column names in csv file
# default fields in yt : numberInProject, summary, description, created, updated, updaterName, resolved,
# reporterName, assigneeName, type, priority, state, subsystem, affectsVersion, voterName, fixedInBuild, permittedGroup
csvClient.FIELDS = dict({
    "summary"           :   "Summary",
    "description"       :   "Description",
    "type"              :   "Issue Type",
    "priority"          :   "Priority",
    "assigneeName"      :   "Assignee",
    "reporterName"      :   "Reporter",
    "created"           :   "Created",
    "updated"           :   "Updated",
    "resolved"          :   "Resolved",
    "affectsVersion"    :   "Affects Version/s",
    "fixedVersion"      :   "Fix Version/s",
    "subsystem"         :   "Component/s",
    "tags"              :   "Multi Issue Keys",
    "state"             :   "Resolution",
    "numberInProject"   :   "Key"
})
# values that should be ignored in particular column
# this value would have the same effect as if the cell is empty
csvClient.IGNORE_VALUES = dict({
    "assigneeName"      :   "Unassigned"
                               })
# maps values in cells of particular column to the yt_values
# f.e. it can be useful for such fields as priority, type etc
csvClient.VALUES = dict({
    "type"      : {"Bug" : "Bug", "Improvement" : "Feature", "New Feature" : "Feature",
                   "Sub-task" : "Task", "Task" : "Task", "Wish" : "Feature"},
    "priority"  : {"Major" : "2", "Trivial" : "4", "Minor" : "3", "Blocker" : "0"},
    "state"     : {"UNRESOLVED" : "Submitted", "Fixed" : "Fixed", "Duplicate" : "Duplicate",
                   "Not A Bug" : "Won't fix", "Cannot Reproduce" : "Can't Reproduce"}
              })
# declares which type of enum should be used for CF
# if cf is not in this list it will be "string" type
csvClient.CUSTOM_FIELD_TYPES = dict([])
# default values for the YT fields
# it is useful for non optional fields
csvClient.DEFAULT_VALUES = {
    "summary"           :   "summary",
    "created"           :   str(int(time() * 1000)),
    "reporterName"      :   "guest",
    "type"              :   "Bug",
    "priority"          :   "3",
    "state"             :   "Submitted"
}

# delimiter in your csv file
csvClient.CSV_DELIMITER = ","
# email which would be set to all imported users
csvClient.DEFAULT_EMAIL = "test@example.com"
# use this setting ONLY if you have number ID (no letters or punctuation)
csvClient.GENERATE_ID_FOR_ISSUES = False
# represents the format of the string (see http://docs.python.org/library/datetime.html#strftime-strptime-behavior)
# format symbol "z" doesn't wok sometimes, maybe you will need to change csv2youtrack.to_unix_date(time_string)
csvClient.DATE_FORMAT_STRING = "%d/%b/%y %I:%M %p"

  