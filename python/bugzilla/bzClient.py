import MySQLdb
import MySQLdb.cursors
from bugzilla import *
import time

class Client(object) :

    def __init__(self, host, port, login, password, db_name = "bugs") :
        self.sql_cnx = MySQLdb.connect(host = host, port = port, user = login, passwd = password,
                                       db = db_name, cursorclass = MySQLdb.cursors.DictCursor, charset = "cp866")
        self.db_host = "%s:%s/" % (host, str(port))

    def get_bz_users(self) :
        cursor = self.sql_cnx.cursor()
        user_id_row = 'userid'
        login_name_row = 'login_name'
        real_name_row = 'realname'
        request = "SELECT %s, %s, %s FROM profiles" % (user_id_row, login_name_row, real_name_row)
        cursor.execute(request)
        result = list([])
        for row in cursor :
            user = BzUser(row[user_id_row])
            user.login = row[login_name_row]
            user.email = row[login_name_row]
            user.full_name = row[real_name_row]
            result.append(user)
        return result

    def get_project_description(self, product_id) :
        cursor = self.sql_cnx.cursor()
        description_row = "description"
        request = "SELECT %s FROM products WHERE id = %s" % (description_row, product_id)
        cursor.execute(request)
        desc = cursor.fetchone()[description_row].encode('utf8')
        return desc

    def get_components(self, product_id) :
        cursor = self.sql_cnx.cursor()

        id_row = 'id'
        description_row = 'description'
        initial_owner_row = 'initialowner'
        name_row = 'name'

        request = "SELECT %s, %s, %s, %s " % (id_row, description_row, initial_owner_row, name_row)
        request += "FROM components WHERE product_id = %s" % product_id

        cursor.execute(request)

        result = list([])
        for row in cursor :
            cmp = BzComponent(row[id_row])
            cmp.description = row[description_row].encode('utf8')
            cmp.initial_owner = self.get_login_by_id(row[initial_owner_row])
            cmp.name = row[name_row].encode('utf8')
            result.append(cmp)
        return result

    def get_versions(self, product_id) :
        cursor = self.sql_cnx.cursor()
        id_row = 'id'
        value_row = 'value'
        request = "SELECT %s, %s FROM versions WHERE product_id = %s" % (id_row, value_row, product_id)
        cursor.execute(request)
        result = list([])
        for row in cursor :
            version = BzVersion(row[id_row])
            version.value = row[value_row].encode('utf8')
            result.append(version)
        return result

    def get_platforms(self) :
        cursor = self.sql_cnx.cursor()
        value_row = 'value'
        request = "SELECT %s FROM rep_platform" % value_row
        cursor.execute(request)
        result = list([])
        for row in cursor :
            result.append(row[value_row])
        return result

    def get_op_systems(self) :
        cursor = self.sql_cnx.cursor()
        value_row = 'value'
        request = "SELECT %s FROM op_sys" % value_row
        cursor.execute(request)
        result = list([])
        for row in cursor :
            result.append(row[value_row])
        return result

    def get_custom_fields(self) :
        cursor = self.sql_cnx.cursor()
        name_row = 'name'
        type_row = 'type'
        request = "SELECT %s, %s FROM fielddefs WHERE (custom = 1) AND NOT (type = 6)" % (name_row, type_row)
        cursor.execute(request)
        result = list([])
        for row in cursor :
            cf = BzCustomField(row[name_row][3:])
            cf.type = str(row[type_row])
            if cf.type in ["2", "3"]:
                values_cursor = self.sql_cnx.cursor()
                value_row = 'value'
                request = "SELECT %s FROM %s" % (value_row, row[name_row])
                values_cursor.execute(request)
                for v in values_cursor :
                    value = v[value_row]
                    if value != "---":
                        cf.values.append(value)
            result.append(cf)
        return result

    def get_issue_link_types(self) :
        cursor = self.sql_cnx.cursor()
        name_row = 'name'
        description_row = 'description'
        request = "SELECT %s, %s FROM fielddefs WHERE (custom = 1) AND (type = 6)" % (name_row, description_row)
        cursor.execute(request)
        result = list([])
        for row in cursor :
            link_type = BzIssueLinkType(row[name_row][3:])
            link_type.description = row[description_row].encode('utf8')
            result.append(link_type)
        return result

    def get_issue_links(self) :
        link_types = self.get_issue_link_types()
        result = set([])
        if not len(link_types):
            return result
        request = "SELECT bug_id, product_id, "
        for elem in link_types :
            request = request + "cf_" + elem.name + ", "
        request = request[:-2]
        request += " FROM bugs"
        cursor = self.sql_cnx.cursor()
        cursor.execute(request)
        for row in cursor :
            bug_id = row['bug_id']
            for type in link_types :
                target = row["cf_" + type.name]
                if target is not None:
                    link = BzIssueLink(type.name, str(bug_id), str(target))
                    link.source_product_id = str(row["product_id"])
                    link.target_product_id = str(self.get_product_id_by_bug_id(target))
                    result.add(link)
        return result

    def _get_component_by_id(self, component_id):
        cursor = self.sql_cnx.cursor()
        name_row = 'name'
        request = "SELECT %s FROM components WHERE id = %s" % (name_row, component_id)
        cursor.execute(request)
        result = cursor.fetchone()
        if result is None:
            return "No subsystem"
        else :
            return result[name_row]

    def get_issues(self, product_id) :
        cursor = self.sql_cnx.cursor()

        assigned_to_row = 'assigned_to'
        id_row = 'bug_id'
        severity_row = 'bug_severity'
        status_row = 'bug_status'
        component_row = 'component_id'
        creation_row = 'creation_ts'
        keywords_row = 'keywords'
        op_row = 'op_sys'
        priority_row = 'priority'
        platform_row = 'rep_platform'
        reporter_row = 'reporter'
        resolution_row = 'resolution'
        desc_row = 'short_desc'
        version_row = 'version'
        votes_row = 'votes'

        request = "SELECT %s, %s, %s, %s, %s, " % (assigned_to_row, id_row, severity_row, status_row, component_row)
        request += "%s, %s, %s, %s, %s, " % (creation_row, keywords_row, op_row, priority_row, platform_row)
        request += "%s, %s, %s, %s, %s " % (reporter_row, resolution_row, desc_row, version_row, votes_row)
        request += "FROM bugs WHERE product_id = %s" % product_id

        cursor.execute(request)
        result = list([])
        cf_cursor = self.sql_cnx.cursor()
        name_row = 'name'
        type_row = 'type'
        cf_request = "SELECT %s, %s FROM fielddefs WHERE (custom = 1) AND NOT (type = 6)" % (name_row, type_row)
        cf_cursor.execute(cf_request)
        cf_map = dict([])
        for row in cf_cursor :
            cf_map[row[name_row]] = row[type_row]
        for row in cursor :
            issue = BzIssue(str(row[id_row]))
            issue.assignee = self.get_login_by_id(row[assigned_to_row])
            issue.severity = row[severity_row]
            issue.status = row[status_row]
            issue.component = self._get_component_by_id(row[component_row])
            issue.created = time.mktime(row[creation_row].timetuple())+1e-6*row['creation_ts'].microsecond

            # tag
            keywords = row[keywords_row].split(",")
            for kw in keywords :
                kw = kw.strip()
                if kw != "":
                    issue.keywords.add(kw)
            # flags
            issue.flags = self.get_flags_by_id(row[id_row])
            issue.op_sys = row[op_row].encode('utf8')
            issue.priority = row[priority_row]
            issue.platform = row[platform_row].encode('utf8')
            issue.reporter = self.get_login_by_id(row[reporter_row])
            issue.resolution = row[resolution_row]
            issue.summary = row[desc_row]
            issue.version = row[version_row]
            if row[votes_row]:
                issue.voters = self.get_voters_by_id(row[id_row])
            # assignees
            cc_cursor = self.sql_cnx.cursor()
            who_row = 'who'
            request = "SELECT %s FROM cc WHERE bug_id = %s" % (who_row, row[id_row])
            cc_cursor.execute(request)
            for cc in cc_cursor :
                issue.cc.append(self.get_login_by_id(cc[who_row]))
            # custom fields
            cf_values = self.get_cf_values_by_id(cf_map, row[id_row])
            for key in cf_values :
                issue.cf[key] = []
                for elem in cf_values[key] :
                    if elem is not None:
                        if isinstance(elem, unicode):
                            issue.cf[key].append(elem)
                        else :
                            issue.cf[key].append(str(elem))
            # comments
            issue.comments = self.get_comments_by_id(row[id_row])
            # attachments
            issue.attachments = self.get_attachments_by_id(row[id_row])
            result.append(issue)
        return result

    def get_duplicate_links(self) :
        cursor = self.sql_cnx.cursor()
        dupe_row = 'dupe'
        dupe_of_row = "dupe_of"
        request = "SELECT %s, %s FROM duplicates" % (dupe_row, dupe_of_row)
        cursor.execute(request)
        result = set([])
        for row in cursor :
            link = BzIssueLink("Duplicate", str(row[dupe_row]), str(row[dupe_of_row]))
            link.source_product_id = self.get_product_id_by_bug_id(row[dupe_row])
            link.target_product_id = self.get_product_id_by_bug_id(row[dupe_of_row])
            result.add(link)
        return result

    def get_dependencies_link(self) :
        cursor = self.sql_cnx.cursor()
        blocked_row = 'blocked'
        depends_on_row = "dependson"
        request = "SELECT %s, %s FROM dependencies" % (blocked_row, depends_on_row)
        cursor.execute(request)
        result = set([])
        for row in cursor :
            link = BzIssueLink("Depend", str(row[blocked_row]), str(row[depends_on_row]))
            link.source_product_id = self.get_product_id_by_bug_id(row[blocked_row])
            link.target_product_id = self.get_product_id_by_bug_id(row[depends_on_row])
            result.add(link)
        return result

    def get_login_by_id(self, id) :
        cursor = self.sql_cnx.cursor()
        login_name = 'login_name'
        request = "SELECT %s FROM profiles WHERE userid = %s" % (login_name, id)
        cursor.execute(request)
        return cursor.fetchone()[login_name]

    def get_cf_values_by_id(self, cf_map, bug_id) :
        single_fields = list([])
        multiple_fields = list([])
        for key in cf_map :
            if cf_map[key] == 3:
                multiple_fields.append(key)
            else :
                single_fields.append(key)
        result = dict([])
        sing_cursor = self.sql_cnx.cursor()
        if len(single_fields):
            request = "SELECT "
            for elem in single_fields :
                request = request + elem + ", "
            request = request[:-2]
            request += " FROM bugs WHERE bug_id = %s" % (str(bug_id))
            sing_cursor.execute(request)
            for row in sing_cursor :
                for elem in single_fields :
                    if row[elem] != "---":
                        result[elem[3:]] = list([row[elem]])
        for cf in multiple_fields :
            mult_cursor = self.sql_cnx.cursor()
            mult_cursor.execute("SELECT value FROM bug_" + cf + " WHERE bug_id = %s", (str(bug_id)))
            result[cf[3:]] = list([])
            for row in mult_cursor :
                if row['value'] != '---':
                    result[cf[3:]].append(row['value'])
        return result

    def get_comments_by_id(self, bug_id) :
        result = list([])
        cursor = self.sql_cnx.cursor()
        when_row = 'bug_when'
        who_row = 'who'
        text_row = 'thetext'
        request = "SELECT %s, %s, %s FROM longdescs WHERE bug_id = %s" % (when_row, who_row, text_row, str(bug_id))
        cursor.execute(request)
        for row in cursor :
            comment = BzComment(time.mktime(row[when_row].timetuple())+1e-6*row[when_row].microsecond)
            comment.reporter = self.get_login_by_id(row[who_row])
            comment.content = row[text_row]
            result.append(comment)
        return result
        
    def get_attachments_by_id(self, bug_id) :
        result = list([])
        cursor = self.sql_cnx.cursor()
        id_row = 'attach_id'
        created_row = 'creation_ts'
        filename_row = 'filename'
        submitter_row = 'submitter_id'
        request = "SELECT %s, %s, %s, %s " % (id_row, created_row, filename_row, submitter_row)
        request += "FROM attachments WHERE bug_id = %s" % str(bug_id)
        cursor.execute(request)
        for row in cursor :
            file_cursor = self.sql_cnx.cursor()
            data_row = 'thedata'
            file_request = "SELECT %s FROM attach_data WHERE id = %s" % (data_row, str(row[id_row]))
            file_cursor.execute(file_request)
            attach = BzAttachment(row[filename_row])
            attach.content = file_cursor.fetchone()[data_row]
            attach.reporter = self.get_login_by_id(row[submitter_row])
            attach.created = time.mktime(row[created_row].timetuple())+1e-6*row[created_row].microsecond
            result.append(attach)
        return result

    def get_flags_by_id(self, bug_id) :
        result = set([])
        cursor = self.sql_cnx.cursor()
        type_row = 'type_id'
        request = "SELECT %s FROM flags WHERE (bug_id = %s) AND (status = '+')" % (type_row, str(bug_id))
        cursor.execute(request)
        for row in cursor :
            flag_cursor = self.sql_cnx.cursor()
            name_row = 'name'
            flag_request = "SELECT %s FROM flagtypes WHERE id = %s LIMIT 1" % (name_row, str(row[type_row]))
            flag_cursor.execute(flag_request)
            result.add(flag_cursor.fetchone()[name_row].encode('utf8'))
        return result

    def get_voters_by_id(self, bug_id) :
        result = set([])
        cursor = self.sql_cnx.cursor()
        who_row = 'who'
        request = "SELECT %s FROM votes WHERE bug_id = %s" % (who_row, str(bug_id))
        cursor.execute(request)
        for row in cursor :
            result.add(self.get_login_by_id(row[who_row]))
        return result

    def get_product_id_by_bug_id(self, bug_id) :
        cursor = self.sql_cnx.cursor()
        id_row = "product_id"
        request = "SELECT %s FROM bugs WHERE bug_id=%s LIMIT 1" % (id_row, str(bug_id))
        cursor.execute(request)
        return cursor.fetchone()[id_row]


    def get_product_id_by_name(self, name) :
        cursor = self.sql_cnx.cursor()
        id_row = "id"
        name_row = "name"
        request = "SELECT %s, %s FROM products" % (id_row, name_row)
        cursor.execute(request)
        for row in cursor :
            if row[name_row].encode('utf8') == str(name):
                return row[id_row]


    def get_product_names(self) :
        cursor = self.sql_cnx.cursor()
        name_row = "name"
        request = "SELECT %s FROM products" % name_row
        cursor.execute(request)
        result = []
        for row in cursor :
            result.append(row[name_row].encode('utf8'))
        return result

