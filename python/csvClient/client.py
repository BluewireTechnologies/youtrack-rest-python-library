import csv
import csvClient

class Client(object) :

    def __init__(self, file_path) :
        self.file_path = file_path

    def get_distinct(self, key) :
        result = set([])
        reader = csv.reader(open(self.file_path), delimiter = csvClient.CSV_DELIMITER)
        header = reader.next()
        ind = 0
        while (ind < len(header)) and (header[ind].strip() != key):
            ind += 1
        if ind < len(header):
            for row in reader :
                value = row[ind].strip()
                if len(value):
                    result.add(value)
        return result                     


    def get_issue_list(self) :
        reader = csv.reader(open(self.file_path), delimiter = csvClient.CSV_DELIMITER)
        reader.next()
        issues = list([])
        header = self.get_header()
        for row in reader :
            issue = dict([])
            issue["comments"] = list([])
            ind = 0
            for elem in row :
                if ind < len(header):
                    issue[header[ind].strip()] = elem.strip()
                else :
                    issue["comments"].append(elem.strip())
                ind += 1
            issues.append(issue)
        return issues

    def get_header(self) :
        reader = csv.reader(open(self.file_path), delimiter = csvClient.CSV_DELIMITER)
        header = reader.next()
        result = []
        for h in header :
            h = h.strip()
            if h != "":
                result.append(h)
        return result

        
