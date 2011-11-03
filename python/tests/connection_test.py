import random
import unittest
from youtrack import YouTrackException, EnumBundle, EnumField, UserBundle
from youtrack.connection import Connection, youtrack, os, os
import math

class ConnectionTest(unittest.TestCase):

    def setUp(self):
        #self.con = Connection('http://teamsys.intellij.net', 'resttest', 'resttest')
        self.con = Connection("http://localhost:8081", "root", "root")
    def test_getProject(self):
        p = self.con.getProject('SB')
        self.assertEqual(p.id, 'SB')
        self.assertEqual(p.name, 'Sandbox')

    def test_getSubsystems(self):
        subsystems = self.con.getSubsystems('SB')
        default = [s for s in subsystems if s.isDefault][0]
        self.assertTrue(default is not None)        

    def test_getIssue(self):
        i = self.con.getIssue('SB-1')
        self.assertEqual(i.id, 'SB-1')
        self.assertEqual(i.numberInProject, '1')
        self.assertEqual(i.projectShortName, 'SB')

    def test_createIssue(self):
        i = self.con.createIssue('SB', 'resttest', 'Test issue', 'Test description', '2', 'Bug', 'First', 'Open', '', '', '')
        self.assertEqual(i.projectShortName, 'SB')
        self.assertEqual(i.priority, '2')
        self.assertEqual(i.type, 'Bug')
        self.assertEqual(i.subsystem, 'First')

    def test_createIssueAttachment(self):
        i = self.con.createIssue('SB', 'resttest', 'For attachmkents test', 'Test description', '2', 'Bug', 'First', 'Open', '', '', '')
        fname = 'connection_test.py'
        content = open(fname)
        self.con.createAttachment(i.id, fname, content)
        self.assertEqual(fname, self.con.getAttachments(i.id)[0].name)

    def test_createAndDeleteSubsystem(self):
        name = 'Test Subsystem [' + str(random.random()) + "]"
        self.con.createSubsystemDetailed('SB', name, False, 'resttest')
        s = self.con.getSubsystem('SB', name)
        self.assertEqual(s.name, name)
        self.assertEqual(s.isDefault, 'false')
        #todo: uncomment when fix deployed to teamsys
        #self.assertEqual(s.defaultAssignee, 'resttest')
        self.con.deleteSubsystem('SB', name)

    def test_importIssues(self):
        issues = self.con.getIssues("A", "", 0, 10)
        for issue in issues:
            if hasattr(issue, "Assignee"):
                issue["assigneeName"] = issue["Assignee"]
                del issue.Assignee
        self.con.importIssues("B", "assignees", issues)


class EnumBundleTests(unittest.TestCase) :

    def setUp(self):
        self.con = Connection('http://localhost:8081', 'root', 'root')

    def test_01_createBundle(self):
        enum_bundle = EnumBundle()
        enum_bundle.name = "TestEnumBundle"
        enum_bundle.values = []
        value_names = ["first", "second", "third"]
        for vn in value_names :
            element = EnumField()
            element.name = vn
            element.description = vn + " description"
            enum_bundle.values.append(element)
        response = self.con.createBundle(enum_bundle)
        self.assertTrue(response.find("http://unit-258.labs.intellij.net:8080/charisma/rest/admin/customfield/bundle/" + enum_bundle.name) != -1)

    def test_02_getBundle(self):
        enum_bundle = self.con.getBundle("enum", "TestEnumBundle")
        self.assertEquals(enum_bundle.name, "TestEnumBundle")
        values = dict({})
        for elem in enum_bundle.values :
            values[elem.name] = elem.description
        self.assertTrue(len(values.keys()) == 3)
        for name in ["first", "second", "third"] :
            self.assertEquals(values[name], name + " description")

    def test_03_getAllBundles(self):
        bundles = self.con.getAllBundles("enum")
        names = [bundle.name for bundle in bundles]
        self.assertTrue(len(names) == 4)
        for name in names :
            self.assertTrue(name in ["DefaultPriorities", "DefaultTypes", "enum", "TestEnumBundle"])

    def test_04_renameBundle(self):
        enum_bundle = self.con.getBundle("enum", "TestEnumBundle")
        self.con.renameBundle(enum_bundle, "TestEnumBundleNew")
        self.assertRaises(Exception, self.con.getBundle, "enum", "TestEnumBundle")
        # if there is no such bundle exception will be thrown
        self.con.getBundle("enum", "TestEnumBundleNew")

    def test_05_addDeleteValue(self):
        enum_bundle = self.con.getBundle("enum", "TestEnumBundleNew")
        value = EnumField()
        value.name = "Added"
        value.description = "description"
        self.con.addValueToBundle(enum_bundle, value)
        enum_bundle = self.con.getBundle("enum", "TestEnumBundleNew")
        self.assertEquals(len(enum_bundle.values), 4)
        new_value = ""
        for v in enum_bundle.values :
            if v.name == "Added" :
                new_value = v
        self.assertEquals(new_value.description, "description")
        self.con.removeValueFromBundle(enum_bundle, new_value)
        enum_bundle = self.con.getBundle("enum", "TestEnumBundleNew")
        self.assertFalse("Added" in [elem.name for elem in enum_bundle.values])

    def test_06_deleteBundle(self):
        enum_bundle = self.con.getBundle("enum", "TestEnumBundleNew")
        self.con.deleteBundle(enum_bundle)
        self.assertRaises(Exception, self.con.getBundle, "enum", "TestEnumBundleNew")

class UserBundleTests(unittest.TestCase) :
    def setUp(self):
        self.con = Connection('http://localhost:8081', 'root', 'root')

    def test_01_createBundle(self):
        user_bundle = UserBundle()
        user_bundle.name = "TestUserBundle"
        user_bundle.users = [self.con.getUser("alexey.pegov")]
        user_bundle.groups = [self.con.getGroup("scala-developers"), self.con.getGroup("jira-users")]
        response = self.con.createBundle(user_bundle)
        self.assertTrue(response.find(
            "http://unit-258.labs.intellij.net:8080/charisma/rest/admin/customfield/userBundle/" +
            user_bundle.name) != -1)

    def test_02_getBundle(self):
        user_bundle = self.con.getBundle("user", "TestUserBundle")
        self.assertEquals(user_bundle.name, "TestUserBundle")
        user_names = [u.login for u in user_bundle.users]
        group_names = [u.name for u in user_bundle.groups]
        self.assertTrue(len(user_names) == 1)
        self.assertTrue(len(group_names) == 2)
        self.assertTrue("alexey.pegov" in user_names)
        self.assertTrue("scala-developers" in group_names)
        self.assertTrue("jira-users" in group_names)

    def test_03_getAllBundles(self):
        bundles = self.con.getAllBundles("user")
        names = [bundle.name for bundle in bundles]
        self.assertTrue(len(names) == 3)
        for name in names :
            self.assertTrue(name in ["HBR-Assignee", "SP-Assignee", "TestUserBundle"])

    def test_04_renameBundle(self):
        user_bundle = self.con.getBundle("user", "TestUserBundle")
        self.con.renameBundle(user_bundle, "TestUserBundleNew")
        self.assertRaises(Exception, self.con.getBundle, "enum", "TestUserBundle")
        self.con.getBundle("user", "TestUserBundleNew")

    def test_05_addDeleteValue(self):
        user_bundle = self.con.getBundle("user", "TestUserBundleNew")
        new_user = self.con.getUser("alexander.doroshko")
        self.con.addValueToBundle(user_bundle, new_user)
        user_bundle = self.con.getBundle("user", "TestUserBundleNew")
        self.assertEquals(len(user_bundle.users), 2)
        user_names = [u.login for u in user_bundle.users]
        self.assertTrue("alexander.doroshko" in user_names)
        self.assertTrue("alexey.pegov" in user_names)
        self.con.removeValueFromBundle(user_bundle, new_user)
        user_names = [u.login for u in self.con.getBundle("user", "TestUserBundleNew").users]
        self.assertFalse("alexander.doroshko" in user_names)

    def test_06_deleteBundle(self):
        user_bundle = self.con.getBundle("user", "TestUserBundleNew")
        self.con.deleteBundle(user_bundle)
        self.assertRaises(Exception, self.con.getBundle, "user", "TestEnumBundleNew")

if __name__ == '__main__':
    unittest.main()
