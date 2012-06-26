from youtrack.connection import Connection

connection = Connection('some url', 'root', 'root')
for user in connection.getUsers():
    print("yet another")
    if (user.login != 'root') and (user.login != 'guest'):
        connection._reqXml('DELETE', '/admin/user/' + user.login, '')
