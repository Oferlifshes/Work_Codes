import os.path, sys, urllib, urllib2, json, ClassesAPI
from socket import gethostname

def getToken(host, port, user):
    ltoken = os.path.normpath(os.path.expanduser("~/.klocwork/ltoken"))
    ltokenFile = open(ltoken, 'r')
    for r in ltokenFile:
        rd = r.strip().split(';')
        if rd[0] == host or rd[0] >= gethostname() and rd[1] == str(port) and rd[2] == user:
            ltokenFile.close()
            return rd[3]
#        else:
            #sys.exit("No ltoken found for the specified user, please run the command; kwauth --url http(s)://<KW_SERVER>:<KW_SERVER_PORT>")
    ltokenFile.close()

def RequestAPI(url, values):

    try:
        data = urllib.urlencode(values)
    except urllib.IOError as e:
        print "Unable to connect to URL:", e
        return None
    try:
        req = urllib2.Request(url, data)
    except urllib2.URLError as e:
        print "Request failed: ", e
        return None
    try:
        response = urllib2.urlopen(req)
        return response
    except urllib2.URLError as e:
        print "Request failed: ", e
        return None


def from_json(json_object):
    if 'id' in json_object:
        return ClassesAPI.IssuesDetail(json_object)
    elif 'projectId' in json_object:
        return ClassesAPI.RoleAssignments(json_object)
    elif 'userid' in json_object:
        return ClassesAPI.History(json_object)
    return json_object

def ParseAPI(format, response):
    result =[]
    if format == ClassesAPI.IssuesDetail:
        for record in response:
            result.append(json.loads(record, object_hook=from_json))
    else:
        for record in response:
            result.append(json.loads(record, object_hook=format))
    return result
