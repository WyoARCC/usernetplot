#!/bin/python

# Creates two csv files for Gephi of groups and their users.
# One contains data for the nodes, the other for the edges.
# An input file needs to be given as an argument.
# This file should be generated with the following command:
# sacct --starttime MMDDYY -a -P -n -s CD -o User,Account,CPUTimeRAW > input_f
# Replace MMDDYY with the date of when you want data collected back to.
# This currently doesn't support nested groups.
import ldap
import csv
import sys


# Options
groupsToSkip = ['arcc', 'arccinterns', 'bc-201606']

# ARCC employees are members of other projects/groups. If you want them
# displayed, set this to True.
includeARCCUsers = False

# If true, include username label's on username nodes.
# Even with them off, their ID's are still set to their username.
# These can be displayed in overview. but not preview.
# If you want them in preview, set this to True.
# This is off by default, because the plot is messy with them on.
usernamelabels = False

# Get cputime per user and account
# Assume that only argument will be the file with the cpu time data.
try:
    with open(sys.argv[1], 'r') as data:
        lines = data.readlines()
except:
    print "No input file given or file doesn't exist, exiting..."
    sys.exit()

users = {}
accts = {}
total = 0

# Read input file
for line in lines:
    line = line.strip().split('|')
    if line[0]:
        acct = line[1]
        user = line[0]
        cput = int(line[2])
        total += cput
        accts[acct] = accts.get(acct, 0) + cput
        users[user] = users.get(user, 0) + cput

max_users = float(max(users.values()))
max_accts = float(max(accts.values()))


# LDAP Server
srv = 'ldap://arccidm1.arcc.uwyo.edu'

# Setup connection to ldap server.
ad = ldap.initialize(srv)

# Make TLS connection to LDAP server.
# best practice is probably to try/except this.
ad.start_tls_s()
ad.simple_bind_s()

# Open up edges CSV file.
edgesf = open('edges.csv', 'wb')
edges = csv.writer(edgesf, delimiter=',')

# Edge files must have Target and Source as their header.
# The way this is set up, users will be the source, groups will be the target.
# To reverse this, simply switch Target and Source Below.
edges.writerow(["Target", "Source"])

# Open up nodes CSV file.
nodesf = open('nodes.csv', 'wb')
nodes = csv.writer(nodesf, delimiter=',')

# The nodes file holds the info on each node
# The ID can be anything, I've made it the group name/username
# The Label is the label of the node, it's what get displayed on the node
# Color is float between 0 or 1, used to make a heatmap
# The Size is just an integer that is used to set the size of the node
# The type distinguishes between group and user. Users are 0, groups are 1
nodes.writerow(["ID", "Label", "Color", "SizeN", "Type"])

# Perform a search on the server to get subgroups of Mt Moran
# This returns a lot of information on the groups, including the users
base_dn = 'dc=arcc,dc=uwyo,dc=edu'
filt = 'memberOf=cn=mountmoran,cn=groups,cn=accounts,dc=arcc,dc=uwyo,dc=edu'
groups = ad.search_s(base_dn, ldap.SCOPE_SUBTREE, filt)

# Get a list of ARCC users from the ARCC Interns and ARCC groups.
# This is a really messy way of doing it with list comprehension.
skip = [member for members in [group[1]['member'] for group in groups
        if group[1]['cn'][0] == 'arcc' or group[1]['cn'][0] == 'arccinterns']
        for member in members]


for group in groups:
    # get the group name
    g_name = group[1]['cn'][0]

    # get a list of members of group (users and subgroups)
    members = group[1]['member']

    # Skip groups in groupsToSkip.
    if g_name in groupsToSkip:
        continue
    # Write the info for the group in the node file.
    # The group name goes twice, because it's the label and ID.
    # Then goes the 'Color' field, which contains the CPU time used on Mt Moran
    # Last, there is the size field. It is the number of members in the group
    # plus 2 to make group nodes always larger then user nodes.
    row = [g_name, g_name, accts.get(g_name, 0)/max_accts, len(members) + 2, 1]
    nodes.writerow(row)

    # Go through the members, add them to the data file.
    for member in members:
        # Skip ARCC Users if includeARCCUsers is False.
        if not includeARCCUsers and member in skip:
            continue

        # Get the username
        uidi = member.find("uid=")
        user = (member[uidi+4:member.find(",", uidi)])

        # Write the edge from user to group.
        edges.writerow([g_name, user])

        # Write the node info for the users
        row = [user,
               user if usernamelabels else " ",
               users.get(user, 0)/max_users,
               1, 0]
        nodes.writerow(row)


# Close the CSV files
nodesf.close()
edgesf.close()

# Disconnect from the server
ad.unbind()
