#!/usr/bin/env python2
# http://trac-hacks.org/wiki/XmlRpcPlugin
import xmlrpclib
import sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-p", "--password", action="store", type="string", dest="password", help= "trac password")
parser.add_option("--host-name", action="store", type="string", dest="critical_host", help="critical host, reported by nagios")
parser.add_option("--service-state", action="store", type="string", dest="service_state", help="service state (e.g. CRITICAL, reported by nagios")
parser.add_option("--description", action="store", type="string", dest="description", help="nagios $SERVICE/HOSTDESC$, will be used in TRAC summary field")
parser.add_option("--longoutput", action="store", type="string", dest="long_output", help="$LONGSERVICEOUTPUT$, reported by nagios")
parser.add_option("--list-methods", action="store_true", dest="listmethods", help="list xmlrpc methods")
## needed options ##
# * trac host
# * trac user
# * nagios long output / $LONGSERVICEOUTPUT$
# * nagios $SERVICESTATE$ (CRITICAL/OK/WARNING/UNKNOWN)
# * SERVICE stuff is needed for HOST too!

(options, args) = parser.parse_args()

if options.password is None:
    parser.error("please specify a password")

if options.critical_host is None:
    parser.error("please specify a host-name")

if options.service_state is None:
    parser.error("please specify a service-state")

if options.description is None:
    parser.error("please specify a scription")

#######
summary_template = "[" + options.critical_host + "] " + options.service_state + ": " + options.description
comment_template = "and again:\n {{{ \n[" + options.critical_host + "] " + options.service_state + ": " + options.description + "\n" + options.long_output + "\n}}}"
######
print summary_template

### initialize server ###
server = xmlrpclib.ServerProxy("http://nagios:%s@tractest01.jimdo.office/trac/login/xmlrpc" % options.password)
multicall = xmlrpclib.MultiCall(server)

if options.listmethods:
    # FIXME make me a function
    for method in server.system.listMethods():
        multicall.system.methodHelp(method)

    for help in multicall():
        lines = help.splitlines()
        print lines[0]
        print '\n'.join(['  ' + x for x in lines[2:]])
        print
    sys.exit(1)




## search for tickets with same summary_template

# ticket ids that contain the same summary and are not closed! (e.g. an incident that happened alreadyalready  not long time ago
## if there is more than 1 matching ticket, use the one with the highest id
open_ticket_with_same_summary=server.ticket.query("summary=" + summary_template + "&status!=closed")

if open_ticket_with_same_summary:
    # post message to ticket (%LONGOUTPUT)
    server.ticket.update(open_ticket_with_same_summary[0], comment_template)
else:
#elseif tickets open for same $hostname
    open_ticket_for_same_host=server.ticket.query("summary^=[" + options.critical_host + "]&status!=closed")
    if open_ticket_for_same_host:
        server.ticket.update(open_ticket_for_same_host[0], comment_template)


#print duplicate_summarys


#print tickets

#for ticket in server.ticket.query("summary=Intrusion-Detection: Tiger aufsetzen"):
#    multicall.ticket.get(ticket)

print("reached end")
sys.exit(1)

#xmlrpclib.ServerProxy.find_ticket_by_summary = find_ticket_by_summary


def find_ticket_by_summary(self, summary):
    ticket_ids = self.ticket.query('summary^={0}&order=id&desc=1&max=1'.format(summary))
    if ticket_ids:
        ticket_id = ticket_ids.pop()
        ticket = server.ticket.get(ticket_id)
        return ticket





#################
description_template = "ticket description"
REOPEN_THRESHOLD = datetime.datetime.now() - datetime.timedelta(7)
MULTISERVICE_FUCKUP_THERSHOLD = datetime.datetime.now() - datetime.timedelta(0, 0, 15)


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
