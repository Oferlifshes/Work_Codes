import time

class ProjectList:
    def __init__(self, attrs):
        self.name = attrs["name"]
        self.id = attrs["id"]

    def __str__(self):
        result = "%s" % self.name
        return result

class IssuesBuild:
   def __init__(self, attrs) :
      self.id = attrs["id"]
      self.code = attrs["code"]
      self.message = attrs["message"]
      self.severity = attrs["severity"]
      self.severityCode = attrs["severityCode"]
      self.status = attrs["status"]

   def __str__(self) :
      return "[%d] \n\t | \n\tCode %s | Severity: %s(%d) | Status: %s |\n\t" % (
      self.id, self.code, self.severity, self.severityCode, self.status
      )

class History(object):
    def __init__(self,attrs):
        if 'comment' in attrs:
            if attrs["comment"] is not None:
                self.comment = attrs["comment"]
        else:
            self.comment = None
        if 'status' in attrs:
            self.status = attrs["status"]
        else:
            self.status = None
        self.userid = attrs["userid"]
        self.date = time.strftime("%d/%m/%y", time.localtime(attrs["date"] / 1000))

    def __str__(self):
        result = "Date: %s, UserID: %s, Comment change: %s" %(self.date, self.userid, self.comment)

class RoleAssignments(object):
    def __init__(self, attrs):
        self.name = attrs['name']
        if 'projectId' in attrs:
            self.projectId = attrs['projectId']
        else:
            self.projectId = None

class IssuesDetail(object):
    def __init__(self, attrs):
        if 'id' in attrs:
            self.id = attrs["id"]
        else:
            self.id = None
        if 'code' in attrs:
            self.code = attrs["code"]
        else:
            self.code = None
        if 'name' in attrs:
            self.name = attrs['name']
        else:
            self.name = None
        self.severity = attrs["severity"]
        #self.status = attrs["status"]
        if 'history' in attrs:
            self.history = attrs['history']
        else:
            self.history = None

    def __str__(self):
        result = "Id:%s, Code:%s, Name:%s, Severity:%s, History:%s" % (self.id, self.code, self.name, self.severity, self.history)
        return result

class Build:
    def __init__(self, attrs):
        self.id = attrs["id"] # build id
        self.name = attrs["name"] # build name
        self.date = time.strftime("%d/%m/%y", time.localtime(attrs["date"] / 1000)) # build date

    def __str__(self):
        result = "%s: %s" % (self.name, self.date)
        return result