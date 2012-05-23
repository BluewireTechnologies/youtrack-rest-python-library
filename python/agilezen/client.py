import json
import httplib2

class Client:

    def __init__(self, url, api_key):
        self._url = (url[:-1] if (url[-1] == '/') else url)
        self._headers = {"X-Zen-ApiKey": api_key,
                         "Accept"      : "application/json;charset=utf-8"}
        self._http = httplib2.Http()

    def get_projects(self, page=1, page_size=100):
        return self._get_content("/projects?" + self._get_page_query_params(page, page_size))

    def get_project_phases(self, project_id, page=1, page_size=100):
        return self._get_content("/projects/%s/phases?%s" % (project_id, self._get_page_query_params(page, page_size)))

    def get_project_roles(self, project_id, page=1, page_size=100):
        return self._get_content("/projects/%s/roles?%s" % (project_id, self._get_page_query_params(page, page_size)))

    def get_stories_for_project(self, project_id, page=1, page_size=100):
        return self._get_content("/projects/%s/stories?with=comments,details,tags,tasks,metrics&%s" %
                                 (project_id, self._get_page_query_params(page, page_size)))

    def get_attachments(self, project_id, story_id, page=1, page_size=100):
        return self._get_content("/projects/%s/stories/%s/attachments?%s" % (project_id, story_id, self._get_page_query_params(page, page_size)))

    def _get_page_query_params(self, page, page_size):
        return "page=%d&page_size=%d" % (page, page_size)

    def _get_content(self, url):
        response, content = self._get(url)
        return content if response.status == 200 else None

    def _api_url(self):
        return self._url + "/api/v1"

    def _get(self, url):
        response, content = self._http.request(self._api_url() + url, headers = self._headers.copy())
        return response, json.loads(content)


