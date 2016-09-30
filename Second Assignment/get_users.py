############################################################
# Author: Bernardo Meneghini Muschioni                     #
# Date: 05/13/2015                                         #
# Version: 1.0.0                                           #
# Input: JSON configuration file                           #
# Output: JSON users` information file                     #
############################################################

import lmiwbem
import sys
import argparse
import os.path
import json

global source, output, verbose

def main():
    # setup argsparse
    argsparseSetup()
    # establish the connection
    tryCIMOMConnection()

# set up the command line parameters
def argsparseSetup():
    global source, output, verbose
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source",
                        help="the path of the JSON source file")
    parser.add_argument("-o", "--output",
                        help="the path of the output directory")
    parser.add_argument("-v", "--verbose",
                        help="optional parameter; if set, the output files are more verbose about the users",
                        action="store_true")
    args = parser.parse_args()
    source = str(args.source)
    output = args.output
    if args.verbose:
        verbose = True
    else:
        verbose = False

def tryCIMOMConnection():
    # getting all the necessary information in the source file (hosts, user names and passwords)
    lstSettings = decodeConfigurationFile()
    # for each setting, make a new connection and collect the all user`s data
    for setting in lstSettings:
        try:
            hostname = 'http://' + setting[0]
            username = setting[1]
            password = setting[2]
            cls = 'LMI_Account'

            #Connect to CIMOM.
            conn = lmiwbem.WBEMConnection()
            conn.connect(hostname, username, password)

            # Enumerate Instances.
            accounts = conn.EnumerateInstances(
                cls,
                'root/cimv2',
                LocalOnly = False,
                DeepInheritance = True,
                IncludeQualifiers = True,
                IncludeClassOrigin = True,
                PropertyList = None,
            )

            # Disconnect from CIMOM.
            conn.disconnect()
            # Gets all the accounts on the system
            lstAccountsInfo = getAccountsInfo(accounts)
            # Gets all the groups on the system
            lstGroupsInfo = getGroupsInfo(hostname, username, password)
            # Matching all the accounts with the groups
            lstmbyGID = matchAccountsByGroupID(lstAccountsInfo, lstGroupsInfo)
            # Creates the JSON file
            dumpJSON(lstmbyGID, setting[0])
        except lmiwbem.ConnectionError as e:
            print("Connection error. Invalid input parameters.", sys.exc_info()[0])
            pass
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise

# gets the necessary information about the accounts
def getAccountsInfo(accounts):
    lstAccountsInfo = []
	
    # iterating though the elements of the list
    for account in accounts:
        accName = account['Name'] # getting the name of the account
        accHomeDirectory = account['HomeDirectory'] # getting the HomeDirectory of the account
        accUserID = account['UserID'] # getting the UserID of the account
        accGroupID = account['GroupID'] # getting the GroupID of the account
        # Creating a 4 dimensional list with the collected data
        accountInfo = accGroupID, accUserID, accName, accHomeDirectory
        # Adding this list to another general list
        lstAccountsInfo.append(accountInfo)
		
    return sorter(lstAccountsInfo, 1)

# decode the JSON source which contains the configuration settings for connection with CIMOM
def decodeConfigurationFile():
    lstSettings = []
    global source
	
    try:
        # opening the source file
        f = open(source)
        # json decoding creates files as a set of dictionaries and lists
        data = json.load(f)
        # data is now a dictionary
        for item in data['Configurations']: # Navigating into the structure collecting the necessary information
            host = item['Host'] # getting the host name
            username = item['Username'] # getting the user name
            password = item['Password'] # getting the password
            setting = host, username, password
            lstSettings.append(setting)
        return lstSettings
    # handling the exceptions
    except IOError as e:
        print("I/O error({0}): {1}".format(e.errno, e.strerror))
        raise
    except ValueError:
        print("Could not parse the data.")
        raise
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

def sorter(list, flag):
    # flag -> 0 for groups, 1 for users
    if flag:
        sortedList = sorted(list, key=lambda list:(list[3], list[1]), reverse = False)
    else:
        sortedList = sorted(list, key=lambda list:(list[1], list[0]), reverse = False)
    return sortedList

# make a new connection with CIMOM to get all the necessary groups information
def getGroupsInfo(hostname, username, password):
    try:
        cls = 'LMI_Group'
        #Connect to CIMOM.
        conn = lmiwbem.WBEMConnection()
        conn.connect(hostname, username, password)

        # Enumerate Instances.
        groups = conn.EnumerateInstances(
             cls,
            'root/cimv2',
            LocalOnly = False,
            DeepInheritance = True,
            IncludeQualifiers = True,
            IncludeClassOrigin = True,
            PropertyList = None,
        )

        # Disconnect from CIMOM.
        conn.disconnect()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    # gets the group`s name and id
    lstGroupsInfo = []
	
    for group in groups:
        # formatting ID`s string
        groupID = str(group['InstanceID']).replace("LMI:GID:", "")
        groupName = group['Name']
        groupInfo = groupID, groupName
        lstGroupsInfo.append(groupInfo)
    # return a list of sorted groups
    return sorter(lstGroupsInfo, 0)

# match, if possible, accounts with their groups
def matchAccountsByGroupID(lstAccountsInfo, lstGroupsInfo):
    # declaration of the variables
    lstMatchedGroups = []
    lstMatchedAccountsByGroupID = []
    i = 0
	
    # iterating through the lists
    while i < len(lstGroupsInfo):
        j = 0
        while j < len(lstAccountsInfo):
            if lstAccountsInfo[j][0] == lstGroupsInfo[i][0]:
                # if the groupID from account object matches with the id from current the group, append it to the list
                lstMatchedGroups.append(lstAccountsInfo[j])
            j += 1
        # if we have more than 1 element matched, add the matched groups to a second list which will also has the current group`s name
        if len(lstMatchedGroups) > 0:
            # the first dimension of the list will have the group`s name
            lstAux = lstGroupsInfo[i][1], lstMatchedGroups
            lstMatchedAccountsByGroupID.append(lstAux)
        i += 1
		
        # clearing the list
        lstMatchedGroups = []

    return lstMatchedAccountsByGroupID

# this method process a list of data and return a valid json string
def createJsonStructure(data, verbose):
    i = 0
    jsonData = '{"Groups": ['
	
    # each data element represents a unique group
    while i < len(data):
        j = 0
        groupName = str(data[i][0]).replace("'", "")
        jsonData += '{ "Name": "' + groupName + '", "Users": ['
		
        # each sub-elements contains the group name as the first element, and from the second one, all the users data
        while j < len(data[i][1]):
            # if the verbose flag is set
            if verbose:
                userID = str(data[i][1][j][1]).replace("'", "") # getting the user id
                userName = str(data[i][1][j][2]).replace("'", "") # getting the user name
                userHome = str(data[i][1][j][3]).replace("'", "") # getting the user home
                string = '{"Name": "' + userName + '", "Home": "' + userHome + '", "UserID": "' + userID + '"},'
            else:
                userName = str(data[i][1][j][2]).replace("'", "") # getting the user name
                string = '"' + userName + '",'
            # if the current user is the last one from the group, remove the ~,~ that was added at the end of the line
            if j+1 >= len(data[i][1]):
                string = string[:-1]
            j += 1
            jsonData += string
        jsonData += ']},'
		
        # if the current group is the last one from the file, remove the ~,~ that was added at the end of the line
        if i+1 >= len(data):
            jsonData = jsonData[:-1]
        i += 1
		
    jsonData += ']}'
    return jsonData

def dumpJSON(lstAccountsInfo, hostname):
    global output, verbose
    # setting the output path and file name
    fileProperties = os.path.join(output, hostname+".json")
	
    # creating the file
    with open(fileProperties, 'w') as outfile:
        jsonData = createJsonStructure(lstAccountsInfo, verbose)
        parsed = json.loads(jsonData)
        json.dump(parsed, outfile, indent=2, sort_keys = True)
    outfile.close()
	
main()