#!/usr/bin/env python2
# http://trac-hacks.org/wiki/XmlRpcPlugin
import xmlrpclib
import sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-p", "--password", action="store", type="string", dest="password", help= "trac password")
parser.add_option("--host", action="store", type="string", dest="critical_host", help="critical host, reported by nagios")
parser.add_option("-d","--description", action="store", type="string", dest="descprtion", help="nagios $SERVICE/HOSTDESC$, will be used in TRAC summary field")
## needed options ##
# * trac host
# * nagios long output / $LONGSERVICEOUTPUT$
# * nagios $SERVICESTATE$ (CRITICAL/OK - ignore rest)
# * SERVICE stuff is needed for HOST too!

(options, args) = parser.parse_args()

if options.password is None:
    parser.error("please specify a password")

#print options.password

server = xmlrpclib.ServerProxy("http://nagios:%s@tractest01.jimdo.office/trac/login/xmlrpc" % options.password)

multicall = xmlrpclib.MultiCall(server)
for method in server.system.listMethods():
    multicall.system.methodHelp(method)

for help in multicall():
    lines = help.splitlines()
    print lines[0]
    print '\n'.join(['  ' + x for x in lines[2:]])
    print

#multicall = xmlrpclib.MultiCall(server)
#for ticket in server.ticket.query("summary=Intrusion-Detection: Tiger aufsetzen"):
#    multicall.ticket.get(ticket)
#print map(str, multicall())
#
## subject ($@)
#
## check for open ticket with summary = $subject
#len(server.ticket.query("summary=Intrusion-Detection: Tiger aufsetzen"))
#
## found: comment to ticket
## not found: open new ticket
