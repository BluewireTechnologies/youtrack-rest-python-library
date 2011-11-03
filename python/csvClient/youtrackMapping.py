import csvClient
import time

csvClient.FIELDS = {
    "numberInProject"   :   "Issue Id",
    "summary"           :   "Summary",
    "description"       :   "Description",
    "created"           :   "Created",
    "updated"           :   "Updated",
    "resolved"          :   "Resolved",
    "reporterName"      :   "Reporter",
    "assigneeName"      :   "Assignee",
    "type"              :   "Type",
    "priority"          :   "Priority",
    "state"             :   "State",
    "subsystem"         :   "Subsystem",
    "tags"              :   "Tags",
}
csvClient.IGNORE_VALUES = {
    "Assignee"          :   "<no user>",
    "Subsystem"         :   "No subsystem",
    "tags"              :   "Watched Issues"
}
csvClient.IGNORE_COLUMNS = ["Project"]
csvClient.VALUES = {
    "priority"      :   {"Minor" : "4", "Normal" : "3", "Major" : "2", "Critical" : "1", "Show-stoper" : "0"}
}
csvClient.DEFAULT_VALUES = {
    "summary"           :   "summary",
    "created"           :   str(int(time.time() * 1000)),
    "reporterName"      :   "guest",
    "type"              :   "Bug",
    "priority"          :   "1",
    "state"             :   "Submitted"
}
csvClient.DEFAULT_EMAIL = "anna.zhdan@gmail.com"
csvClient.CSV_DELIMITER = ";"
csvClient.GENERATE_ID_FOR_ISSUES = True
csvClient.DATE_FORMAT_STRING = "%A, %B %d, %Y %I:%M:%S %p %Z"