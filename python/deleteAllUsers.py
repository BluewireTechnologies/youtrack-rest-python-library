from youtrack.connection import Connection

connection = Connection('http://jruby.myjetbrains.com/youtrack', 'root', 'root')
for user in connection.getUsers():
    print("yet another")
    if (user.login != 'root') and (user.login != 'guest'):
        connection._reqXml('DELETE', '/admin/user/' + user.login, '')
