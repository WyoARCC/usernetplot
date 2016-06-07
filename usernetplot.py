#!/bin/python

# Creates two csv files for Gephi of groups and their users. One contains data for the nodes, the other for the edges. Both should be imported into Gephi. This currently doesn't support nested groups, but that can be added
import ldap
import csv


# Options
# If true, include the ARCC Group in the plot 
includeARCCGroup = False
# If true, include the ARCC Intern Group in the plot
includeARCCInternGroup = False
# If true, include username label's on username nodes. With them, the plot looks much messier. Even with them off, their ID's are still set to their username. In overview you can display ID's on nodes. This isn't an option in preview however, so if you want them displayed in preview, set this to True.
usernamelabels = False 



# LDAP Server
srv = 'ldap://arccidm1.arcc.uwyo.edu'

# Setup connection to ldap server.
ad = ldap.initialize(srv)

# Make TLS connection to LDAP server.
# best practice is probably to try/except this, but since this is just a script and isn't gonna be used by any end users I won't do that for now.
ad.start_tls_s()
ad.simple_bind_s()

# Open up edges CSV file.
edgesf = open('edges.csv', 'wb')
edges = csv.writer(edgesf, delimiter=',')
# Edge files must have Target and Source as their header. Target is the target of the node, source is the source. The way this is set up, users will be the source, groups will be the target. To reverse this, simply switch Target and Source Below.
edges.writerow(["Target" , "Source"])

# Open up nodes CSV file.
nodesf = open('nodes.csv', 'wb')
nodes = csv.writer(nodesf, delimiter=',')
# The nodes file holds the info on each node. The ID can be anything, but I've made it the cn (username/groupname), the Label is the label of the node, it's what get displayed on the node (also the groupname and username if that option is enabled above), Color is 0 or 1, depending on if the node is a user or group, it's used to set the Color of the node in Gephi, and finally, the Size is just an integer that is used to set the size of the node in Gephi
nodes.writerow(["ID" , "Label", "Color", "SizeN"])

# Perform a search on the server to get the groups that are subgroups of mountmoran. This returns a lot of information on the groups, including the users. 
base_dn = 'dc=arcc,dc=uwyo,dc=edu'
filter_dn = 'memberOf=cn=mountmoran,cn=groups,cn=accounts,dc=arcc,dc=uwyo,dc=edu'
groups =  ad.search_s(base_dn, ldap.SCOPE_SUBTREE, filter_dn)

for group in groups:
    # get the group name
    g_name = group[1]['cn'][0]

    # Skip arcc or arccintern groups depending on the options set at the beginning
    if (g_name == "arcc" and not includeARCCGroup) or (g_name == "arccinterns" and not includeARCCInternGroup):
        continue

    # get a list of members of group (users and subgroups)
    members = group[1]['member']
    # Write the info for the group in the node file. The group name goes twice, because it's the ID and Label, a 1 is set for color, and finally the Size is simply the number of members the group has plus 2. (That way, groups are always larger then users)
    nodes.writerow([g_name] * 2 + [1] + [len(members)+2])
    
    # Go through the members, add them to the data file.
    for member in members:
        uidi = member.find("uid=")
        user = (member[uidi+4:member.find(",",uidi)])
        # Write the edge from user to group.
        edges.writerow([g_name, user]) 
        # Write the node info for the users
        if usernamelabels:
            nodes.writerow([user] * 2 + ["0"] + ["1"]) 
        else:
            nodes.writerow([user] + [" "] + ["0"] + ["1"]) 



# Close the CSV files
nodesf.close()
edgesf.close()


# Disconnect from the server
ad.unbind()
