import csv
import csvClient

class Client(object) :

    def __init__(self, file_path) :
        self._file_path = file_path
        self._issues_reader = self._get_reader()
        self._header = self._read_header()

    def _read_header(self):
        header = self._issues_reader.next()
        return [field_name for field_name in [h.strip() for h in header] if len(field_name)]

    def _get_reader(self):
        return csv.reader(open(self._file_path, "r"), delimiter=csvClient.CSV_DELIMITER)

    def get_issue_list(self, batch_size):
        issues = list([])
        header_len = len(self._header)
        for row in self._issues_reader:
            if batch_size:
                batch_size -= 1
            else:
                break

            issue = {"comments": []}
            for i in range(len(row)):
                value = row[i].strip()
                if len(value):
                    if i < header_len:
                        issue[self._header[i]] = value
                    else:
                        issue["comments"].append(value)
            issues.append(issue)
        return issues

    def get_header(self) :
        return self._header


        
