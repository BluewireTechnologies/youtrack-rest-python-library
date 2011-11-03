
# names of columns which we don't want to import
IGNORE_COLUMNS = []
# maps issue fields with column names in csv file
# default fields in yt : numberInProject, summary, description, created, updated, updaterName, resolved,
# reporterName, assigneeName, type, priority, state, subsystem, affectsVersion, voterName, fixedInBuild, permittedGroup
FIELDS = dict([])
# values that should be ignored in particular column
# this value would have the same effect as if the cell is empty
IGNORE_VALUES = dict([])
# maps values in cells of particular column to the yt_values
# f.e. it can be useful for such fields as priority, type etc
VALUES = dict([])
# declares which type of enum should be used for CF
# if cf is not in this list it will be "string" type
CUSTOM_FIELD_TYPES = dict([])
# default values for the YT fields
# it is useful for non optional fields
DEFAULT_VALUES = dict([])
# delimiter in your csv file
CSV_DELIMITER = ","
# email which would be set to all imported users
DEFAULT_EMAIL = "test@example.com"
# use this setting ONLY if you have number ID (no letters or punctuation)
GENERATE_ID_FOR_ISSUES = True
# represents the format of the string (see http://docs.python.org/library/datetime.html#strftime-strptime-behavior)
# format symbol "z" doesn't wok sometimes, maybe you will need to change csv2youtrack.to_unix_date(time_string)
DATE_FORMAT_STRING = ""
