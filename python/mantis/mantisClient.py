import MySQLdb
import MySQLdb.cursors
from mantis import *
import mantis


class MantisClient(object) :

    def __init__(self, host, port, login, password, db_name, charset_name) :
        self.sql_cnx = MySQLdb.connect(host = host, port = port, user = login, passwd = password,
                                       db = db_name, cursorclass = MySQLdb.cursors.DictCursor, charset = charset_name)


    def get_project_id_by_name(self, project_name) :
        cursor = self.sql_cnx.cursor()
        id_row = "id"
        name_row = "name"
        request = "SELECT %s, %s FROM mantis_project_table" % (id_row, name_row,)
        cursor.execute(request)
        for row in cursor :
            if row[name_row].encode('utf8') == project_name:
                return row[id_row]

    def get_mantis_users(self) :
        cursor = self.sql_cnx.cursor()
        user_name_row = "username"
        real_name_row = "realname"
        email_row = "email"
        request = "SELECT %s, %s, %s FROM mantis_user_table" % (user_name_row, real_name_row, email_row)
        cursor.execute(request)
        result = []
        for row in cursor :
            user = MantisUser(row[user_name_row].replace(" ", "_"))
            user.real_name=row[real_name_row]
            user.email = row[email_row]
            result.append(user)
        return result

    def get_mantis_categories(self, project_id) :
        cursor = self.sql_cnx.cursor()
        project_ids_string = repr(self._calculate_project_ids(project_id)).replace('[','(').replace(']',')')
        name_row = "name"
        user_id_row = "user_id"
        request = "SELECT %s, %s FROM mantis_category_table WHERE project_id IN %s" % (user_id_row, name_row, project_ids_string)
        cursor.execute(request)
        result = []
        for row in cursor :
            category = MantisCategory(row[name_row])
            user_id = row[user_id_row]
            if user_id:
                category.assignee = self.get_user_name_by_id(user_id)
            result.append(category)
        return result

    def get_mantis_versions(self, project_id) :
        cursor = self.sql_cnx.cursor()
        project_ids_string = repr(self._calculate_project_ids(project_id)).replace('[','(').replace(']',')')
        version_row = "version"
        released_row = "released"
        obsolete_row = "obsolete"
        date_order = "date_order"
        request = "SELECT %s, %s, %s, %s FROM mantis_project_version_table " %(version_row, released_row, obsolete_row, date_order)
        request += "WHERE project_id IN %s" % project_ids_string
        cursor.execute(request)
        result = []
        for row in cursor :
            version = MantisVersion(row[version_row])
            version.is_released = (row[released_row] > 0)
            version.is_obsolete = (row[obsolete_row] > 0)
            version.release_date = self._to_epoch_time(row[date_order])
            result.append(version)
        return result

    def get_mantis_custom_fields(self, project_ids) :
        cursor = self.sql_cnx.cursor()
        ids = set([])
        for project_id in project_ids :
            ids = ids | set(self._calculate_project_ids(project_id))
        project_ids_string = repr(list(ids)).replace('[','(').replace(']',')')
        cf_ids_request = "SELECT DISTINCT field_id FROM mantis_custom_field_project_table WHERE project_id IN " + project_ids_string
        id_row = "id"
        type_row = "type"
        name_row = "name"
        default_value_row = "default_value"
        possible_values_row = "possible_values"
        request = "SELECT %s, %s, %s, %s, %s " % (id_row, name_row, type_row, possible_values_row, default_value_row)
        request += "FROM mantis_custom_field_table WHERE %s IN (%s)" % (id_row, cf_ids_request)
        cursor.execute(request)
        result = []
        for row in cursor :
            cf = MantisCustomFieldDef(row[id_row])
            cf.type = row[type_row]
            cf.name = row[name_row]
            cf.default_value = row[default_value_row]
            if row[type_row] in [3, 6, 7, 9, 5]:
                # possible values
                values = row[possible_values_row].split("|")
                cf.values = []
                for v in values :
                    v = v.strip()
                    if v != "":
                        cf.values.append(v)
            result.append(cf)
        return result

    def get_custom_fields_attached_to_project(self, project_id) :
        cursor = self.sql_cnx.cursor()
        project_ids = (repr(self._calculate_project_ids(project_id)).replace('[','(').replace(']',')'))
        field_id_row = "field_id"
        request = "SELECT DISTINCT %s FROM mantis_custom_field_project_table WHERE project_id IN %s" % (field_id_row, project_ids)
        cursor.execute(request)
        result = []
        for row in cursor :
            result.append(row[field_id_row])
        return result


    def get_mantis_issues(self, project_id) :
        cursor = self.sql_cnx.cursor()
        project_ids = (repr(self._calculate_project_ids(project_id)).replace('[','(').replace(']',')'))
        id_row = "id"
        project_id_row = "project_id"
        reporter_id_row = "reporter_id"
        handler_id_row = "handler_id"
        bug_text_id_row = "bug_text_id"
        summary_row = "summary"
        category_id_row = "category_id"
        date_submitted_row = "date_submitted"
        due_date_row = "due_date"
        last_updated_row = "last_updated"

        issue_string = "SELECT %s, %s, %s, %s, %s, " % (id_row, project_id_row, reporter_id_row, handler_id_row, bug_text_id_row)
        issue_string += "%s, %s, %s, %s, %s " % (summary_row, category_id_row, date_submitted_row, due_date_row, last_updated_row)
        request = issue_string + " FROM mantis_bug_table WHERE project_id IN " + project_ids
        cursor.execute(request)
        result = []
        for row in cursor :
            issue = MantisIssue(row[id_row])
            reporter_id = row[reporter_id_row]
            if reporter_id:
                issue.reporter_name = self.get_user_name_by_id(reporter_id)
            handler_id = row[handler_id_row]
            if handler_id:
                issue.cf_values["handler"] = [self.get_user_name_by_id(handler_id)]

            self._set_int_issue_parameters(issue)
            self._set_issue_text_fields(issue, row[bug_text_id_row])
            self._set_os_issue_parameters(issue)
            self._set_version_issue_parameters(issue)

            issue.cf_values["subproject"] = [self._get_project_name_by_id(row[project_id_row])]
            issue.summary = row[summary_row]
            issue.cf_values["category"] = [self._get_category_by_id(row[category_id_row])]
            issue.date_submitted = self._to_epoch_time(row[date_submitted_row])
            issue[due_date_row] = self._to_epoch_time(row[due_date_row])
            issue.last_updated = self._to_epoch_time(row[last_updated_row])
            #custom fields

            cf_cursor = self.sql_cnx.cursor()
            cf_cursor.execute("SELECT field_id, value FROM mantis_custom_field_string_table WHERE bug_id=%s",
                              (str(row["id"]),))
            for row in cf_cursor :
                issue_cf = self._get_cf_name_by_id(row["field_id"])
                value = row["value"]
                if issue_cf["type"] in [3, 6, 7, 9, 5]:
                    values = value.split("|")
                    issue.cf_values[issue_cf["name"]] = []
                    for v in values :
                        v = v.strip()
                        if v != "":
                            issue.cf_values[issue_cf["name"]].append(v)
                elif issue_cf["type"] == 8:
                    issue.cf_values[issue_cf["name"]] = self._to_epoch_time(value) if len(value) else ""
                else :
                    issue.cf_values[issue_cf["name"]] = value
            issue.tags = self._get_issue_tags_by_id(issue.id)
            issue.comments = self._get_comments_by_id(issue.id)
            result.append(issue)
        return result

    def get_mantis_subprojects(self, project_id) :
        cursor = self.sql_cnx.cursor()
        project_ids = (repr(self._calculate_project_ids(project_id)).replace('[','(').replace(']',')'))
        name_row = "name"
        request = "SELECT %s FROM mantis_project_table WHERE id IN %s" % (name_row, project_ids)
        cursor.execute(request)
        result = []
        for row in cursor :
            result.append(row[name_row])
        return result

    def get_issue_links(self) :
        cursor = self.sql_cnx.cursor()
        result = []
        cursor.execute("SELECT * FROM mantis_bug_relationship_table")
        for row in cursor:
            source_bug_id = row["source_bug_id"]
            target_bug_id = row["destination_bug_id"]
            link = MantisIssueLink(source_bug_id, target_bug_id, row["relationship_type"])
            link.source_project_id = self._get_project_id_by_bug_id(source_bug_id)
            link.target_project_id = self._get_project_id_by_bug_id(target_bug_id)
            result.append(link)
        return result

    def get_mantis_attachments(self, project_id):
        cursor = self.sql_cnx.cursor()
        project_ids = (repr(self._calculate_project_ids(project_id)).replace('[','(').replace(']',')'))
        id_row = "id"
        issue_ids_request = "SELECT %s FROM mantis_bug_table WHERE project_id IN %s" % (id_row, project_ids)
        request = "SELECT id FROM mantis_bug_file_table WHERE bug_id IN (%s)" % issue_ids_request
        cursor.execute(request)
        result = []
        for row in cursor:
            result.append(MantisAttachment(row[id_row], self.sql_cnx))
        return result


    def get_project_description(self, project_id) :
        cursor = self.sql_cnx.cursor()
        description_row = "description"
        cursor.execute("SELECT %s FROM mantis_project_table WHERE id=%s LIMIT 1", (description_row, str(project_id)))
        description = cursor.fetchone()[description_row]
        if description is None:
            return "empty description"
        return description.encode('utf8')

    def get_user_name_by_id(self, id) :
        cursor = self.sql_cnx.cursor()
        user_name_row = "username"
        request = "SELECT %s FROM mantis_user_table WHERE id=%s LIMIT 1" % (user_name_row, str(id))
        cursor.execute(request)
        element = cursor.fetchone()
        if element is not None:
            return element[user_name_row].replace(" ", "_")
        else :
            return "guest"

    def _calculate_project_ids(self, project_id) :
        result = self._get_child_projects_by_project_id(project_id)
        result.append(int(project_id))
        result.append(int(0))
        return result

    def _get_child_projects_by_project_id(self, id) :
        cursor = self.sql_cnx.cursor()
        child_id_row = "child_id"
        request = "SELECT %s FROM mantis_project_hierarchy_table WHERE parent_id = %s" % (child_id_row, id)
        cursor.execute(request)
        result = []
        for row in cursor :
            result.append(int(row[child_id_row]))
            result.extend(self._get_child_projects_by_project_id(row[child_id_row]))
        return result


    def _set_issue_text_fields(self, issue, text_id) :
        cursor = self.sql_cnx.cursor()
        description_row = "description"
        steps_row = "steps_to_reproduce"
        additional_row = "additional_information"
        request = "SELECT %s, %s, %s " % (description_row, steps_row, additional_row)
        request += "FROM mantis_bug_text_table WHERE id=%s LIMIT 1" % str(text_id)
        cursor.execute(request)
        row = cursor.fetchone()
        issue.description = row[description_row]
        issue.steps_to_reproduce = row[steps_row]
        issue.additional_information = row[additional_row]

    def _get_category_by_id(self, id) :
        cursor = self.sql_cnx.cursor()
        name_row = "name"
        request = "SELECT %s FROM mantis_category_table WHERE id=%s LIMIT 1" % (name_row, str(id))
        cursor.execute(request)
        category = cursor.fetchone()
        if category is None:
            return "No subsystem"
        else :
            return category[name_row]

    def _get_comments_by_id(self, id) :
        cursor = self.sql_cnx.cursor()
        reporter_id_row = "reporter_id"
        bugnote_row = "bugnote_text_id"
        date_submitted_row = "date_submitted"
        request = "SELECT %s, %s, %s" % (reporter_id_row, bugnote_row, date_submitted_row)
        request += " FROM mantis_bugnote_table WHERE bug_id=%s" % str(id)
        cursor.execute(request)
        result = []
        for row in cursor :
            text_cursor = self.sql_cnx.cursor()
            note_row = "note"
            req = "SELECT %s FROM mantis_bugnote_text_table WHERE id=%s LIMIT 1" % (note_row, str(row[bugnote_row]))
            text_cursor.execute(req)
            comment = MantisComment()
            comment.reporter = self.get_user_name_by_id(row[reporter_id_row])
            comment.date_submitted = self._to_epoch_time(row[date_submitted_row])
            comment.text = text_cursor.fetchone()[note_row]
            result.append(comment)
        return result

    def _get_project_id_by_bug_id(self, bug_id) :
        cursor = self.sql_cnx.cursor()
        project_id_row = "project_id"
        request = "SELECT %s FROM mantis_bug_table WHERE id=%s LIMIT 1" % (project_id_row, bug_id)
        cursor.execute(request)
        return cursor.fetchone()[project_id_row]


    def _get_cf_name_by_id(self, id) :
        cursor = self.sql_cnx.cursor()
        cursor.execute("SELECT name, type  FROM mantis_custom_field_table WHERE id=%s LIMIT 1", (str(id),))
        return cursor.fetchone()

    def _set_int_issue_parameters(self, issue) :
        cursor = self.sql_cnx.cursor()
        priority_row = "priority"
        severity_row = "severity"
        reproducibility_row = "reproducibility"
        status_row = "status"
        resolution_row = "resolution"

        request = "SELECT %s, %s, %s, %s, %s " % (priority_row, severity_row, reproducibility_row, status_row, resolution_row)
        request += "FROM mantis_bug_table WHERE id=%s LIMIT 1" % str(issue.id)
        cursor.execute(request)
        row = cursor.fetchone()
        issue.cf_values[priority_row] = [mantis.PRIORITY_VALUES[row[priority_row]]]
        issue.cf_values[severity_row] = [mantis.SEVERITY_VALUES[row[severity_row]]]
        issue.cf_values[reproducibility_row] = [mantis.REPRODUCIBILITY_VALUES[row[reproducibility_row]]]
        issue.cf_values[status_row] = [mantis.SEVERITY_VALUES[row[status_row]]]
        issue.cf_values[resolution_row] = [mantis.RESOLUTION_VALUES[row[resolution_row]]]

    def _set_os_issue_parameters(self, issue) :
        cursor = self.sql_cnx.cursor()
        os_row = "os"
        os_build_row = "os_build"
        platform_row = "platform"
        request = "SELECT %s, %s, %s " % (os_row, os_build_row, platform_row)
        request += "FROM mantis_bug_table WHERE id=%s LIMIT 1" % str(issue.id)
        cursor.execute(request)
        row = cursor.fetchone()
        issue.cf_values[os_row] = [row[os_row]]
        issue.cf_values[os_build_row] = [row[os_build_row]]
        issue.cf_values[platform_row] = [row[platform_row]]

    def _set_version_issue_parameters(self, issue) :
        cursor = self.sql_cnx.cursor()
        version_row = "version"
        fixed_in_version_row = "fixed_in_version"
        build_row = "build"
        target_version_row = "target_version"
        request = "SELECT %s, %s, %s, %s" % (version_row, fixed_in_version_row, build_row, target_version_row)
        request += " FROM mantis_bug_table WHERE id=%s LIMIT 1" % str(issue.id)
        cursor.execute(request)
        row = cursor.fetchone()
        issue.cf_values[version_row] = [row[version_row]]
        issue.cf_values[fixed_in_version_row] = [row[fixed_in_version_row]]
        issue.cf_values[build_row] = [row[build_row]]
        issue.cf_values[target_version_row] = [row[target_version_row]]

    def _get_project_name_by_id(self, id) :
        cursor = self.sql_cnx.cursor()
        name_row = "name"
        request = "SELECT %s FROM mantis_project_table WHERE id=%s LIMIT 1" % (name_row, str(id))
        cursor.execute(request)
        return cursor.fetchone()[name_row]

    def _get_issue_tags_by_id(self, id) :
        cursor = self.sql_cnx.cursor()
        name_row = "name"
        request = "SELECT %s FROM mantis_tag_table WHERE id IN (SELECT tag_id FROM mantis_bug_tag_table WHERE bug_id = %s) LIMIT 1" % (name_row, str(id))
        cursor.execute(request)
        result = []
        for row in cursor :
            result.append(row[name_row])
        return result

    def _to_epoch_time(self, time_string):
        if len(time_string) :
            return str(int(time_string) * 1000)
        return ""