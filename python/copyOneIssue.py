# this script helps to move issue from one youtrack instance to another
import sys

def main() :
    try :
        source_url, source_login, source_password, source_issue_id, target_url, target_login = sys.argv[1:7]
        target_password, target_project_id = sys.argv[7:9]
    except :
        print "Usage : "
        print "copyOneIssue source_url source_login source_password source_issue_id target_url target_login target_password target_project_id"

def doCopy(source_url, source_login, source_password, source_issue_id, target_url, target_login, target_password, target_project_id) :
    print "source_url : " + source_url
    print "source_login : " + source_login
    print "source_password : " + source_password
    print "source_issue_id : " + source_issue_id
    print "target_url : " + target_url
    print "target_login : " + target_login
    print "target_password : " + target_password
    print "target_project_id : " + target_project_id

if __name__ == "__main__":
    main()
  