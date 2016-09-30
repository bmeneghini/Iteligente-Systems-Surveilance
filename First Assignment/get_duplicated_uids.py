import argparse
import csv
import pyldap
import sys

def main():
    # Setup the argsparse
    cnProject, outputName, flagD = argsparseSetup()
    # Getting all the members and their details of the given project
    lstMembers, lstuidNumbers = tryConection(cnProject)
    # Finding all the members that have duplicated uidNumber
    lstDuplicated = list(findDuplicates(lstuidNumbers))
    # Matching the duplicated uidNumbers with their corresponding members
    lstResult = matchDuplicates(lstDuplicated, lstMembers)
    # Sorting the list
    sorter(lstResult, flagD)
    # Writing the CSV file with the final result
    writeCSVFile(lstResult, outputName)     

'''
Function name: argsparseSetup
Parameters: none
Summary: Setup the command line parameters
'''
def argsparseSetup():    
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--project",
                        help="the title (CN attribute) of the project, whose members should be inspected (compulsory, string type).")
    parser.add_argument("-o", "--output", 
                        help="the path of the output file (compulsory, string type).")
    parser.add_argument("-d", "--descending",  
                        help="optional, flag type. If it is set, the order of the records in the output file should be descending (otherwise ascending).",
                        action="store_true")
    args = parser.parse_args()
    cnProject = str(args.project)
    outputName = args.output
    if args.descending:
        flagD = True
    else:
        flagD = False
    return cnProject, outputName, flagD

'''
Function name: sorter
Parameters: list l, bool flagD
Summary: Return a sorted list based on a given flag, true = descending, false = ascending
'''
def sorter(l, flagD):
    sortedList = sorted(l, key=lambda l:(l[0], l[1]), reverse = flagD)
    return sortedList

'''
Function name: findDuplicates
Parameters: list lstuidNumbers
Summary: Returns a list with the duplicated elements of a given list
'''
def findDuplicates(lstuidNumbers):
    lstDUplicateNumbers = set([x for x in lstuidNumbers if lstuidNumbers.count(x) > 1])
    return lstDUplicateNumbers

'''
Function name: matchDuplicates
Parameters: list lstDuplicated, list lstMembers
Summary: Return a unique list of members with only the entries which repeated the uidNumber
'''
def matchDuplicates(lstDuplicated, lstMembers):
    lstResult = []
    i = 0
    while(i < len(lstDuplicated)):
        j = 0
        while(j < len(lstMembers)):
            if lstDuplicated[i] == lstMembers[j][0]:
                lstResult.append(lstMembers[j])
            j += 1    
        i += 1
    return lstResult
 
'''
Function name: getMemberDetails
Parameters: string completeMember
Summary: Return a tridimensional list with the uidNumber, cnMember and the description of a given object member 
''' 
def getMemberDetails(completeMember):
    for member in completeMember:
        uidNumber = str(member['uidNumber']).replace("'","")
        cn = str(member['cn']).replace("'","")
        description = str(member['description']).replace("'","")
        lstDetails = uidNumber, cn, description
    return lstDetails

'''
Function name: getMemberUID
Parameters: string completeMember
Summary: Return the uidNumber of a given object member 
'''
def getMemberUID(completeMember):
    for member in completeMember:
        uidNumber = str(member['uidNumber']).replace("'","")
    return uidNumber

'''
Function name: tryProjectConection
Parameters: string cnProject, connection conn
Summary: Query for a specific project on the LDAP database
'''
def tryProjectConection(cnProject, conn):
    projects = conn.search(
                       "ou=projects,dc=irf,dc=local",
                       1,
                       "(&(objectClass=groupOfNames)(cn=%s)(!(cn=projectsstaff)))" % (cnProject),
                       attrlist=['cn','member']
                       )
    if(sys.getsizeof(projects) == None):
        print("ERROR: Project is invalid.")
        raise SystemExit
    return projects

'''
Function name: getLists
Parameters: object projects, connection conn
Summary: Query all the members of a project and returns a list of it and its uidNumbers
'''	
def getLists(projects, conn):
    for project in projects:
            lstuidNumbers = []
            lstMembers = []
            for member in project['member']:
                strMember = str(member).lower().split(sep=',', maxsplit=1)
                cnMember = strMember[0].split(sep='=')[1]
                
                completeMember = conn.search(
                   "%s" %(strMember[1]),
                   1,
                   "(&(objectClass=inetOrgPerson)(cn=%s)(!(cn=projectsstaff)))" % (cnMember),
                   attrlist=['cn','uidNumber', 'description']
                   )
                
                lstMembers.append(getMemberDetails(completeMember))
                lstuidNumbers.append(getMemberUID(completeMember))
    return lstMembers, lstuidNumbers

'''
Function name: writeCSVFile
Parameters: list lstMembers, string outputName
Summary: Write on a CSV file the list which contains the final result
'''
def writeCSVFile(lstMembers, outputName):
    with open(outputName, 'w', newline='', encoding='utf-8') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['[uidNumber]'] + ['[CN]'] + ['[Corporation]'])
        for item in lstMembers:
            spamwriter.writerow([str(item)])

'''
Function name: tryConection
Parameters: string cnProject
Summary: Connect to the LDAP database fetching for all the necessary information and returning the formated members list.
'''			
def tryConection(cnProject):
    conn = None
    connectionClosed = True
    try:
        client = pyldap.LDAPClient("ldap://localhost:389")
        conn = client.connect()
        connectionClosed = False
    
        projects = tryProjectConection(cnProject, conn)
        lstMembers, lstuidNumbers = getLists(projects, conn)
        
        conn.close()
        connectionClosed = True
        
        return lstMembers, lstuidNumbers
     
    except pyldap.ConnectionError:
        print("ERROR: Connection to the LDAP Server has been terminated.")
    finally:
        if (conn is not None) and (not connectionClosed):
            conn.close()

main()