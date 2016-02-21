import urllib, urllib2, json, sys, os.path, getpass

def getToken(host, port, user):
    ltoken = os.path.normpath(os.path.expanduser("~/.klocwork/ltoken"))
    ltokenFile = open(ltoken, 'r')
    for r in ltokenFile:
        rd = r.strip().split(';')
        if rd[0] == host and rd[1] == str(port) and rd[2] == user:
            ltokenFile.close()
            return rd[3]
    ltokenFile.close()

class Details(object):
    def __init__(self, attrs):
        self.id = attrs["id"]
        self.code = attrs["code"]
        self.name = attrs["name"]
        self.location = attrs["location"]
        self.build = attrs["build"]
        self.severity = attrs["severity"]
        self.owner = attrs["owner"]
        self.state = attrs["state"]
        self.status = attrs["status"]
        self.history = attrs["history"]
        if "xSync" in attrs:
            self.xsync = attrs["xsync"]
        else:
            self.xsync = None

    def __str__(self):
        result = "Id:%s, Code:%s, Name:%s, Location:%s, Build:%s, Severity:%s, Owner:%s, State:%s, Status:%s, History:%s" % (self.id, self.code, self.name, self.location, self.build, self.severity, self.owner, self.state, self.status, self.history)
        if self.xsync != None:
                        result = result + ", XSyncInfo:%s" % self.xsync
        return result

def from_json(json_object):
    #print json_object
    return Details(json_object)

def report(url, user, action, project, id, xsync=None):
    values = {"user": user, "action": action, "project": project, "id": id}
    if xsync is not None:
        values['include_xsync'] = xsync
    loginToken = getToken(host, port, user)
    if loginToken is not None:
        values["ltoken"] = loginToken
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    result = []
    for record in response:
        #print "R:" ,record
        result.append(from_json(json.loads(record)))
    return result

host = "localhost"
port = 8080
user = getpass.getuser()
action = "issue_details"
url = "http://%s:%d/review/api" % (host, port)
project = "myproject"
id = "1"
xsync="false"

issue_details = report(url, user, action, project, id, xsync)
print "Issue Details:"
for details in issue_details:
    print details

