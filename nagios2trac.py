#!/usr/bin/env python

# python 2.6
# http://trac-hacks.org/wiki/XmlRpcPlugin
import xmlrpclib
import sys
import ConfigParser
import os
import datetime
from optparse import OptionParser
import logging

SERVER = None
TRAC_NOTIFICATIONS = None
COMMENT_TEMPLATE = None


def get_options_and_args(argv):
    parser = OptionParser()

    parser.add_option("--host-name", action="store", type="string", dest="critical_host", help="critical host, reported by nagios")
    parser.add_option("--service-state", action="store", type="string", dest="service_state", help="service state (e.g. CRITICAL, reported by nagios")
    parser.add_option("--description", action="store", type="string", dest="description", help="nagios $SERVICE/HOSTDESC$, will be used in TRAC summary field")
    parser.add_option("--longoutput", action="store", type="string", dest="long_output", help="$LONGSERVICEOUTPUT$, reported by nagios")
    parser.add_option("-c", "--config", action="store", type="string", dest="config", default="/etc/nagios3/nagios2trac.conf", help="path to configfile, defaults to /etc/nagios3/nagios2trac.conf")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="more verbosive output")
    parser.add_option("--new-ticket-threshold", action="store", type="int", dest="new_ticket_threshold", help="create a new ticket if existing one has not been modified since <int> minutes")
    parser.add_option("--list-methods", action="store_true", dest="listmethods", help="list xmlrpc methods (debug)")

    (options, args) = parser.parse_args(argv)

    # FIXME - beautify
    if options.critical_host is None and not options.listmethods:
        parser.error("please specify a host-name")

    if options.service_state is None and not options.listmethods:
        parser.error("please specify a service-state")

    if options.description is None and not options.listmethods:
        parser.error("please specify a description")

    if options.long_output is None and not options.listmethods:
        parser.error("please specify a longoutput")

    if options.debug:
        logging.getLogger().level = logging.DEBUG

    return options, args

### functions ###


def debug_output(output):
    logging.debug(output)


def create_ticket(summary_template, description_template, trac_owner):
    SERVER.ticket.create(summary_template, description_template, {'owner': trac_owner, 'type': 'Incident', 'priority': 'critical'}, TRAC_NOTIFICATIONS)
    debug_output("created a new ticket with summary:" + summary_template + " and owner " + trac_owner)


def create_ticket_if_not_recovered(summary_template, description_template, trac_owner, service_recovered):
    if not service_recovered:
        debug_output("service or host not recovered. creating a new ticket")
        create_ticket(summary_template, description_template, trac_owner)
    else:
        debug_output("service or host recovered, though not creating a new ticket")


def update_ticket(ticket_id):
    SERVER.ticket.update(ticket_id, COMMENT_TEMPLATE, {}, TRAC_NOTIFICATIONS)
    debug_output("update ticket %d" % ticket_id)


def read_config(options):
    global TRAC_NOTIFICATIONS
    if not os.access(options.config, os.R_OK):
        print('configfile "' + options.config + '" does not exist or is not readable')
        print("exiting..")
        sys.exit(1)

    # read config
    config = ConfigParser.ConfigParser()
    config.read(options.config)

    trac_host = config.get('Trac', 'host')
    trac_user = config.get('Trac', 'user')
    trac_password = config.get('Trac', 'password')
    trac_owner = config.get('Trac', 'ticket_owner')
    TRAC_NOTIFICATIONS = config.get('Trac', 'notifications')
    trac_new_ticket_threshold = int(config.get('Trac', 'new_ticket_threshold'))

    return trac_host, trac_user, trac_password, trac_owner, trac_new_ticket_threshold


def list_methods():
    multicall = xmlrpclib.MultiCall(SERVER)

    # FIXME make me a function
    for method in SERVER.system.listMethods():
        multicall.system.methodHelp(method)

    for help in multicall():
        lines = help.splitlines()
        print lines[0]
        print '\n'.join(['  ' + x for x in lines[2:]])
        print


### /functions ###

def main(options, args):
    global SERVER, COMMENT_TEMPLATE
    trac_host, trac_user, trac_password, trac_owner, trac_new_ticket_threshold = read_config(options)

    # prefer cli option over configfile
    new_ticket_threshold = options.new_ticket_threshold or trac_new_ticket_threshold

    ### initialize SERVER ###
    SERVER = xmlrpclib.ServerProxy("https://%s:%s@%s/trac/login/xmlrpc" % (trac_user, trac_password, trac_host))

    if options.listmethods:
        list_methods()
        sys.exit(1)

    #######
    summary_template = "[" + options.critical_host + "] " + options.service_state + ": " + options.description
    # optparser escapes \n, so it is not possible to add newlines into the longoutput that are actually interpreted by trac
    # we workaround this by "unescaping" all escaped \n
    # this is only needed inside COMMENT_TEMPLATE because the trac summary can online contain a single line
    comment_template_plain = "{{{ \n[" + options.critical_host + "] " + options.service_state + ": " + options.description + "\n" + options.long_output + "\n}}}"
    COMMENT_TEMPLATE = comment_template_plain.replace('\\n', '\n')
    description_template = """=== Incident ===
    * Does it affect only one user/colleague? Not an incident, normal support case.
    * What has been noticed? (e.g. nagios check + host that failed)
    """ + COMMENT_TEMPLATE + """
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

    ## it this a recovery message? ##

    service_recovered = options.service_state.startswith(('OK', 'UP'))

    ## search for tickets with same summary_template

    # ticket ids that contain the same summary and are not closed! (e.g. an incident that happened already not long time ago
    # if there is more than 1 matching ticket, use the one with the highest id
    open_ticket_with_same_summary = SERVER.ticket.query("summary=" + summary_template + "&status!=closed")

    if open_ticket_with_same_summary:
        # post message to ticket
        update_ticket(open_ticket_with_same_summary[0])
        debug_output("appended to ticket #%d because of FULL summary match" % open_ticket_with_same_summary[0])
    else:
        #elseif tickets open for same $hostname
        open_ticket_for_same_host = SERVER.ticket.query("summary^=[" + options.critical_host + "]&status!=closed")
        if open_ticket_for_same_host:
            # check last modified time of existing ticket
            last_modified_utc = SERVER.ticket.get(open_ticket_for_same_host[0])[2]

            # we need the localtime in utc too
            current_time_utc = datetime.datetime.utcnow()

            current_time_minus_threshold = current_time_utc - datetime.timedelta(minutes=new_ticket_threshold)

            if last_modified_utc < current_time_minus_threshold:
                debug_output("ticket has not been modified for more than the configured threshold value (%d) minutes, trying to create a new one" % new_ticket_threshold)
                create_ticket_if_not_recovered(summary_template, description_template, trac_owner, service_recovered)
            else:
                update_ticket(open_ticket_for_same_host[0])
                debug_output("appended to ticket #%d because of hostname match" % open_ticket_for_same_host[0])
        else:
            debug_output("creating a new ticket")
            create_ticket_if_not_recovered(summary_template, description_template, trac_owner, service_recovered)

    debug_output("reached end")

if __name__ == "__main__":
    options, args = get_options_and_args(sys.argv[1:])
    main(options, args)
    sys.exit(0)
