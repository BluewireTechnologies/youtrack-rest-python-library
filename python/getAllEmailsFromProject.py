from youtrack.connection import Connection

target = Connection("some url", "root", "root")
for user in target.getUsers() :
    yt_user = target.getUser(user.login)
    try :
        if (str(yt_user.email).find("jetbrains") > 0) :
            print yt_user.email
        elif (str(yt_user.email).find("intellij") > 0) :
            print yt_user.email
    except :
        print "exception"