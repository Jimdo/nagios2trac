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

# FIXME - beautify
if options.password is None and not options.listmethods:
    parser.error("please specify a password")

if options.critical_host is None and not options.listmethods:
    parser.error("please specify a host-name")

if options.service_state is None and not options.listmethods:
    parser.error("please specify a service-state")

if options.description is None and not options.listmethods:
    parser.error("please specify a scription")

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


#######
summary_template = "[" + options.critical_host + "] " + options.service_state + ": " + options.description
comment_template = "{{{ \n[" + options.critical_host + "] " + options.service_state + ": " + options.description + "\n" + options.long_output + "\n}}}"
description_template = """=== Incident ===
 * Does it affect only one user/colleague? Not an incident, normal support case.
 * What has been noticed? (e.g. nagios check + host that failed)
""" + comment_template + """
 * Who is affected? (all users, limited set of users, departments, partners, ...)
 * When did it start? (e.g. nagios reported time)
 * How did you notice it (Monitoring, Support..?)

=== Spread the word first, then act ===
 * Always put a link to this ticket everywhere you inform your colleagues about it
 * Tell Yammer group "System Status" when the incident started (latest 30min after incident notice!)
 * Update Yammer at least every hour for incidents during office hours, even if nothing changed.
 * Be available in Infrastruktur channel and communicate to your colleagues
 * Announce waiting times longer than one hour (e.g. waiting for the hosting provider) as "time for next update"

 * Update Ticket and Yammer AFTER incident is over, too.

=== Recommended Checks and Actions ===
 * [wiki:NuetzlicheShell], [wiki:AdminHandbuch]

=== Ask for Help (esp. during office hours) ===
 * Get help at big incidents and pair the incident
 * Ask for help in communication/documentation for bigger incidents

=== Post Mortem Analysis ===
 * How has it been resolved? What was the fix?
 * How was the issue triggered? What have been the circumstances?
 * What was affected? (see Incident, Who is already documented there)
 * How can this situation be avoided in the future? (only relevant if "rule of three" triggered or effect is considered "major" by the team)
 * Did a known standard solution work? If not: Document it! e.g. in [wiki:NuetzlicheShell], [wiki:AdminHandbuch]
 * Close the ticket, if no further actions can be derived from it.
"""
######

mail_notifications=True
assign_to_user='bonko'

## search for tickets with same summary_template


# ticket ids that contain the same summary and are not closed! (e.g. an incident that happened already not long time ago
# if there is more than 1 matching ticket, use the one with the highest id
open_ticket_with_same_summary=server.ticket.query("summary=" + summary_template + "&status!=closed")

if open_ticket_with_same_summary:
    # post message to ticket
    server.ticket.update(open_ticket_with_same_summary[0], comment_template,{},mail_notifications)
    print("appended to a ticket because of FULL summary match")
else:
    #elseif tickets open for same $hostname
    open_ticket_for_same_host=server.ticket.query("summary^=[" + options.critical_host + "]&status!=closed")
    if open_ticket_for_same_host:
        # maybe only post if last edit time > 15 min to prevent trac spam when many services of a host fail
        server.ticket.update(open_ticket_for_same_host[0], comment_template,{},mail_notifications)
        print("appended to a ticket because of hostname match")
    else:
        # create a new ticket
        # replace comment_template with description_template(contains incident template)
        server.ticket.create(summary_template,description_template,{'owner': assign_to_user, 'type': 'Incident', 'priority': 'critical'},mail_notifications)
        print("created a new ticket")



print("reached end")
sys.exit(1)

#################
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
