import json, AccessControl, getpass, ClassesAPI, sys
from copy import copy
import time
import csv


def main():
    log = open("log-"+str(time.strftime("%d.%m.%y", time.localtime())),'w')
    ServerData, values = Initial_Script_Data(log)

    Projects_List = Get_Projects_List(ServerData["url"], values, log)
    Project_Report = {}

    fieldnames = ["Project Name", "Project Managers", "Date of latest analysis", "Date of previous analysis", "Critical Issues", "Error Issues",
                  "Critical Ignored Issues", "Error Ignored Issues","Ignored without comments", "Complexity Approved", "Complexity Disapproved",
                  "Top 10 Disapproved Complexity ID","Top 10 Disapproved Complexity Score", "Comments" ]

    with open(ServerData["FILE_PATH"]+'\\'+ServerData["FILE_NAME"]+r'.csv', 'wb') as csvfile:
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames, dialect="excel")
        writer.writeheader()
        for project in Projects_List:

            if project is not None:
                values['project'] = str(project.name)
                log.write("****RETRIEVING INFORMATION FOR PROJECT: %s ****\n\n" %str(project.name))
                temp_project = Get_Builds_List(ServerData["url"], values, log)

                temp_project.update(Get_Project_Managers(ServerData, values, project, log))

                temp_project.update(Get_NotIgnored_Issues(ServerData, values, log))

                temp_project.update(Get_Ignored_Issues(ServerData, values, log))

                temp_project.update(Get_Complexity_Issues(ServerData,values, log))

                Project_Report[project.name] = temp_project

                Write_Report_To_File(Project_Report, project, writer)
                log.write("\n")
            else:
                log.write("Error: Project not found!, project value is %s" %project)
    print("Report successfully generated")
    log.write("Report successfully generated")

def Write_Report_To_File(Project_Report, project, writer):
    """Write Project Report rows as csv file with Excel dialect"""

    writer.writerow({"Project Name": project.name,
                     "Project Managers": Project_Report[project.name]["Project_Managers"],
                     "Date of latest analysis": Project_Report[project.name]["last_build"],
                     "Date of previous analysis": Project_Report[project.name]["prev_build"],
                     "Critical Issues": Project_Report[project.name]["crit_issues"],
                     "Error Issues": Project_Report[project.name]["err_issues"],
                     "Critical Ignored Issues": Project_Report[project.name]["crit_ignore"],
                     "Error Ignored Issues": Project_Report[project.name]["err_ignore"],
                     "Ignored without comments": Project_Report[project.name]["no_message_ignore_id"],
                     "Complexity Approved": Project_Report[project.name]["complex_approved"],
                     "Complexity Disapproved": Project_Report[project.name]["complex_not_approved"],
                     "Top 10 Disapproved Complexity ID": str(
                         [detail[0] for detail in Project_Report[project.name]["ComplexityDetails"]]).strip('[]'),
                     "Top 10 Disapproved Complexity Score": str(
                         [detail[1] for detail in Project_Report[project.name]["ComplexityDetails"]]).strip('[]')})

def Get_Project_Managers(ServerData, values, project, log):
    """Find users of the role defined in ServerDate["ManagerRole"] and match them to projects by their projectId.
    Note: Users in the specified role without a specified project will not be entered to any project"""

    vals = copy(values)
    vals['action'] = "role_assignments"
    vals['search'] = ServerData["ManagerRole"]
    temp = {}
    proj_managers = []
    log.write("Getting project managers, query:\n %s" %vals)
    Response = AccessControl.RequestAPI(ServerData['url'], vals)
    for record in Response:
        for assignment in json.loads(record)['assignments']:
            if assignment['projectId'] == project.id:
                proj_managers.append(str(assignment['name']))
    temp["Project_Managers"] = ', '.join(proj_managers)

    return temp

def Get_Ignored_Issues(ServerData, values, log):
    """Get summary of all ignored issues where Severity is Critical/Error and Code is NOT ServerData["ComplexityCode"]
    and issue ID of ignored issues without related comment"""

    temp_ignored = {}
    issue_id = []
    vals = copy(values)
    val = copy(values)
    vals['action'] = "search"

    for i in 1, 2:  # find all ignore Critical and Error issues

        vals["query"] = "severity:%d status:ignore -code:%s grouping:%s" % (i,ServerData["ComplexityCode"],ServerData["Grouping"])
        log.write("Getting not-ignored issues, query:\n %s" %vals)
        Response = AccessControl.RequestAPI(ServerData["url"], vals)
        Result = AccessControl.ParseAPI(ClassesAPI.IssuesBuild, Response)

        val["action"] = "issue_details"

        for issue in Result:  # Search for ignored issues without comments
            val["id"] = issue.id
            response = AccessControl.RequestAPI(ServerData["url"], val)
            issue_details = AccessControl.ParseAPI(ClassesAPI.IssuesDetail, response)

            for index in range(len(issue_details[0].history)):
                if issue_details[0].history[index].status == u'Ignore':
                    if issue_details[0].history[index].comment == u'':
                        if (index-1) < 0:
                            issue_id.append(issue.id)
                            break
                        elif issue_details[0].history[index-1].comment == u'':
                            issue_id.append(issue.id)
                            break

        if i == 1:
            temp_ignored["crit_ignore"] = len(Result)

        elif i == 2:
            temp_ignored["err_ignore"] = len(Result)

    temp_ignored["no_message_ignore_id"] = str(issue_id).strip('[]')
    return temp_ignored

def Get_NotIgnored_Issues(ServerData, values, log):
    """Appends into "temp_project" data on non-ignored issues: 1) Sum of Critical issues
                                                               2) Sum of Error issues
                                                               3) Data of Complexity issues - assuming complexity issues are classified as Critical/Error"""
    temp ={}
    vals = copy(values)
    vals['action'] = "search"

    for i in 1, 2:  # find all non-ignore Critical and Error issues
        vals["query"] = "severity:%d -status:ignore -code:%s grouping:%s" % (i, ServerData["ComplexityCode"], ServerData["Grouping"])
        log.write("Getting ignored issues, query:\n %s" %vals)
        Response = AccessControl.RequestAPI(ServerData["url"], vals)
        Result = AccessControl.ParseAPI(ClassesAPI.IssuesBuild, Response)

        if i == 1:

            temp["crit_issues"] = len(Result)

        elif i == 2:

            temp["err_issues"] = len(Result)

    return temp

def Get_Complexity_Issues(ServerData, values, log):
    """Appends into temp_project data about complexity issues: 1) Sum of "Approved" issues - status: Not a problem
                                                               2) Sum of "Not approved" issues - Status != Not a problem
                                                               3) Issue ID and complexity value of top 10 most complex "Not approved" issues - as a tuple"""

    vals = copy(values)
    vals['action'] = 'search'
    vals['query'] = "code:%s" % ServerData["ComplexityCode"]
    log.write("Getting complexity issues, query:\n %s" %vals)
    complex_approve = 0
    complex_not_approve = 0
    complex_details = []

    temp_complex = {}

    import re
    Response = AccessControl.RequestAPI(ServerData["url"], vals)
    Result = AccessControl.ParseAPI(ClassesAPI.IssuesBuild, Response)

    for issue in Result:
        if issue.status == "Not a Problem":
            complex_approve += 1

        else:
            complex_not_approve += 1

            x = str(issue.message)
            y = re.search("[0-9]+(?=>)", x)
            y = int(y.group())
            complex_details.append((issue.id, y))

    complex_details = sorted(complex_details, key=lambda score: score[1], reverse=True)
    temp_complex["complex_approved"] = complex_approve
    temp_complex["complex_not_approved"] = complex_not_approve
    temp_complex["ComplexityDetails"] = complex_details[:10]

    return temp_complex

def Get_Builds_List(url, values, log):
    """Returns the first and second latest list of builds for the project in values['project'], and N/A if either one does not exist"""

    vals = copy(values)
    temp_project = {}
    vals["action"] = "builds"
    log.write("Getting builds list, query:\n %s" %vals)
    Response = AccessControl.RequestAPI(url, vals)
    Result = AccessControl.ParseAPI(ClassesAPI.Build, Response)

    if len(Result) > 0:  # Find latest and second latest build dates and names

        temp_project["last_build"] = Result[0].date
        if len(Result) > 1:
            temp_project["prev_build"] = Result[1].date
        else:
            temp_project["prev_build"] = "N/A"


    else:
        temp_project["last_build"] = "N/A"
        temp_project["prev_build"] = "N/A"

    return temp_project

def Get_Projects_List(url, values, log):
    """Get the list of projects from Klocwork server address defined in ServerData["url"]"""

    vals = copy(values)
    vals["action"] = "Projects"
    log.write("Getting projects list, query:\n %s\n" %vals)
    Response = AccessControl.RequestAPI(url, vals)
    Result = AccessControl.ParseAPI(ClassesAPI.ProjectList, Response)
    return Result

def Initial_Script_Data(log):
    """Initialize configuration settings from 'config.txt' that resides inside same directory as python script:
                                          1) Defined code of Complexity issues
                                          2) Defined Project Manager role
                                          3) Grouping - default is "off"
                                          4) Klocwork server address
                                          5) Klocwork server port
                                          6) User with sufficient permissions to run the script - default is currently logged in user"""
    from os import path
    from sys import executable
    ServerData = {}
    '''If run from Python shell/not from PyInstaller executable, replace "path.dirname(executable)" with "path.dirname(__file__) in this function'''
    with open(path.dirname(__file__)+'\\'+'config.txt','r') as config:
        for line in config:
            temp_line = line.split('=', 1)
            if len(temp_line) > 2:
                exit("Config file syntax is incorrect!")
            else:
                ServerData[temp_line[0]] = temp_line[1].replace('\n','')

    if ServerData["KW_SERVER"] is '':
        ServerData["KW_SERVER"] = "localhost"
    if ServerData["KW_SERVER_PORT"] is '':
        ServerData["KW_SERVER_PORT"] = "8080"
    if ServerData["USER"] is '':
        ServerData["USER"] = getpass.getuser()
    if ServerData["Grouping"] is '':
        ServerData["Grouping"] = "off"
    if ServerData["FILE_PATH"] is '':
        ServerData["FILE_PATH"] = path.dirname(__file__)
    if ServerData["FILE_NAME"] is '':
        import time
        ServerData["FILE_NAME"] = time.strftime("%d.%m.%y", time.localtime())


    url = "http://%s:%s/review/api" % (ServerData["KW_SERVER"], ServerData["KW_SERVER_PORT"])
    ServerData["url"] =  url
    print("Server configurations are:")
    print("KW_SERVER: %s" %ServerData["KW_SERVER"])
    print("KW_SERVER_PORt: %s" %ServerData["KW_SERVER_PORT"])
    print("USER: %s" %ServerData["USER"])
    print("FILE_PATH: %s" %ServerData["FILE_PATH"])
    print("FILE_NAME: %s" %ServerData["FILE_NAME"])
    print("ComplexityCode: %s" %ServerData["ComplexityCode"])
    print("ManagerRole: %s" %ServerData["ManagerRole"])
    print("Grouping: %s" %ServerData["Grouping"])
    log.write("Server configurations are:")
    log.write("KW_SERVER: %s" %ServerData["KW_SERVER"])
    log.write("KW_SERVER_PORt: %s" %ServerData["KW_SERVER_PORT"])
    log.write("USER: %s" %ServerData["USER"])
    log.write("FILE_PATH: %s" %ServerData["FILE_PATH"])
    log.write("FILE_NAME: %s" %ServerData["FILE_NAME"])
    log.write("ComplexityCode: %s" %ServerData["ComplexityCode"])
    log.write("ManagerRole: %s" %ServerData["ManagerRole"])
    log.write("Grouping: %s" %ServerData["Grouping"])
    values = {"user": ServerData["USER"]}
    loginToken = AccessControl.getToken(ServerData["KW_SERVER"], ServerData["KW_SERVER_PORT"], ServerData["USER"])
    if loginToken is not None:
        values["ltoken"] = loginToken
    else:
        return None

    return ServerData, values

if __name__ == "__main__": main()