import csvClient
import time


csvClient.IGNORE_COLUMNS = ["milestone"]
csvClient.FIELDS = {
    "numberInProject"   :   "id",
    "summary"           :   "summary",
    "state"             :   "status",
    "type"              :   "type",
    "priority"          :   "priority",
    "subsystem"         :   "component",
    "fixedVersion"      :   "version",
    "reporterName"      :   "reporter",
    "tags"              :   "keywords",
    "watcherName"       :   "cc",
    "created"           :   "time",
    "updated"           :   "changetime",
    "assigneeName"      :   "owner"
}
csvClient.IGNORE_VALUES = {
    "resolution"        :   "--",
    "radio_field"       :   "--",
    "select_field"      :   "--",
    "checkbox_field"    :   "--",
    "text_field"        :   "--",
    "owner"             :   "somebody",
    "reporter"          :   "anonymous"
}
csvClient.VALUES = {
    "type"     :   {"enhancement" : "Feature", "defect" : "Bug", "task" : "Task"},
    "state"    :   {"accepted" : "Submitted", "new" : "Open", "reopened" : "Reopened",
                    "assigned" : "Submitted", "closed" : "Fixed"},
    "priority" :   { "trivial" : "4", "minor" : "3", "major" : "2", "critical" : "1", "blocker" : "0"}
}
csvClient.CUSTOM_FIELD_TYPES = {
    "radio_field"       :   "enum[1]",
    "select_field"      :   "enum[1]",
    "checkbox_field"    :   "enum[*]"
}
csvClient.DEFAULT_VALUES = {
    "summary"           :   "summary",
    "created"           :   str(int(time.time() * 1000)),
    "reporterName"      :   "guest",
    "type"              :   "Bug",
    "priority"          :   "1",
    "state"             :   "Submitted"
}
csvClient.CSV_DELIMITER = ","
csvClient.DEFAULT_EMAIL = "anna.zhdan@gmail.com"
csvClient.GENERATE_ID_FOR_ISSUES = False
csvClient.DATE_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"