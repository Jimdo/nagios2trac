#!/usr/bin/env python2
# http://trac-hacks.org/wiki/XmlRpcPlugin
import xmlrpclib
import sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-p", "--password", action="store", type="string", dest="password", help= "trac password")
parser.add_option("--host", action="store", type="string", dest="critical_host", help="critical host, reported by nagios")
parser.add_option("-d","--description", action="store", type="string", dest="description", help="nagios $SERVICE/HOSTDESC$, will be used in TRAC summary field")
## needed options ##
# * trac host
# * trac user
# * nagios long output / $LONGSERVICEOUTPUT$
# * nagios $SERVICESTATE$ (CRITICAL/OK/WARNING/UNKNOWN)
# * SERVICE stuff is needed for HOST too!

(options, args) = parser.parse_args()

if options.password is None:
    parser.error("please specify a password")

#print options.password

def find_ticket_by_summary(self, summary):
    ticket_ids = self.ticket.query('summary^={0}&order=id&desc=1&max=1'.format(summary))
    if ticket_ids:
        ticket_id = ticket_ids.pop()
        ticket = server.ticket.get(ticket_id)
        return ticket

xmlrpclib.ServerProxy.find_ticket_by_summary = find_ticket_by_summary

server = xmlrpclib.ServerProxy("http://nagios:%s@tractest01.jimdo.office/trac/login/xmlrpc" % options.password)

summary_template = "[{host}] {service_state}: {description}"
comment_template = "It happened again!\n{LONGSERVICEOUTPUT}"
description_template = "ticket description"
REOPEN_THRESHOLD = datetime.datetime.now() - datetime.timedelta(7)
MULTISERVICE_FUCKUP_THERSHOLD = datetime.datetime.now() - datetime.timedelta(0, 0, 15)

multicall = xmlrpclib.MultiCall(server)
for method in server.system.listMethods():
    multicall.system.methodHelp(method)

for help in multicall():
    lines = help.splitlines()
    print lines[0]
    print '\n'.join(['  ' + x for x in lines[2:]])
    print

print server.ticket.query('summary^=[Nagios]')


def create_tickets(nagios_input, trac_api):
    if nagios_input['service_state'] != 'OK':
        return

    summary = summary_template.format(nagios_input)
    comment = comment_template.format(nagios_input)
    description = description_template.format(nagios_input)

    ticket = trac_api.find_ticket_by_summary(summary)

    if ticket:
        if ticket.status != 'closed':
            trac_api.post_to_ticket(ticket, comment)
        else:
            if ticket.changed < REOPEN_THRESHOLD:
                trac_api.reopen_ticket(ticket)
                trac_api.post_to_ticket(ticket, comment)
            else:
                trac_api.open_ticket(summary, description)

    else:
        ticket = trac_api.find_open_ticket_by_host_name(host_name)
        if ticket and ticket.changed < MULTISERVICE_FUCKUP_THERSHOLD: # we found a fresh and open ticket for this host
            trac_api.post_to_ticket(ticket, comment)
        else:
            trac_api.open_ticket(summary, description)

    trac_api.commit()

create_tickets(nagios_input, server)
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
