import unittest
from StringIO import StringIO
import sys
import itertools
import datetime

from mock import Mock


class TestFunctions(unittest.TestCase):

    def setUp(self):
        import nagios2trac
        self.nagios2trac = nagios2trac
        self.nagios2trac.SERVER = Mock()
        self.options_dict = {'--host-name': 'myhost', '--service-state': 'CRITICAL', '--description': 'myservice running', '--longoutput': 'loooong', '--config': 'nagios2trac.conf.default'}
        options_list = list(itertools.chain(*self.options_dict.items()))
        self.options, self.args = self.nagios2trac.get_options_and_args(options_list)
        self.summary_template = '[myhost] CRITICAL: myservice running'

    def testOpenTicketWithSameSummary(self):
        self.nagios2trac.open_ticket_with_same_summary(self.summary_template)
        self.nagios2trac.SERVER.ticket.query.assert_called_with("summary=" + self.summary_template + "&status!=closed&order=id&desc=true")

    def testOpenTicketForSameHost(self):
        self.nagios2trac.open_ticket_for_same_host(self.options.critical_host)
        self.nagios2trac.SERVER.ticket.query.assert_called_with("summary^=[" + self.options.critical_host + "]&status!=closed&order=id&desc=true")


class TestNagios2Trac(unittest.TestCase):

    def setUp(self):
        import nagios2trac
        self.nagios2trac = nagios2trac
        self.options_dict = {'--host-name': 'myhost', '--service-state': 'CRITICAL', '--description': 'myservice running', '--longoutput': 'loooong', '--config': 'nagios2trac.conf.default'}
        # convert dict to flat list
        options_list = list(itertools.chain(*self.options_dict.items()))
        self.options, self.args = self.nagios2trac.get_options_and_args(options_list)
        self.nagios2trac.xmlrpclib = Mock()
        self.nagios2trac.update_ticket = Mock()
        self.nagios2trac.create_ticket = Mock()
        self.nagios2trac.open_ticket_with_same_summary = Mock()
        self.nagios2trac.open_ticket_for_same_host = Mock()
        self.nagios2trac.create_ticket_if_not_recovered = Mock()
        self._stderr = sys.stderr
        sys.stderr = StringIO()
        self.trac_owner = 'sometracuser'
        self.new_ticket_threshold = 120
        self.summary_template = '[myhost] CRITICAL: myservice running'
        self.comment_template_plain = "{{{ \n[myhost] CRITICAL: myservice running\nloooong\n}}}"
        self.COMMENT_TEMPLATE = self.comment_template_plain.replace('\\n', '\n')
        self.description_template = """=== Incident ===
    * Does it affect only one user/colleague? Not an incident, normal support case.
    * What has been noticed? (e.g. nagios check + host that failed)
    """ + self.COMMENT_TEMPLATE + """
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

    def testNeedsHostname(self):
        try:
            del self.options_dict['--host-name']
            options_list = list(itertools.chain(*self.options_dict.items()))
            self.nagios2trac.get_options_and_args(options_list)
        except SystemExit, e:
            self.assertEquals(e.code, 2)
            self.assertTrue('error: please specify a host-name' in sys.stderr.getvalue())
        else:
            self.fail('Did not raise SystemExit')

    def testNeedsServicestate(self):
        try:
            del self.options_dict['--service-state']
            options_list = list(itertools.chain(*self.options_dict.items()))
            self.nagios2trac.get_options_and_args(options_list)
        except SystemExit, e:
            self.assertEquals(e.code, 2)
            self.assertTrue('error: please specify a service-state' in sys.stderr.getvalue())
        else:
            self.fail('Did not raise SystemExit')

    def testNeedsDescription(self):
        try:
            del self.options_dict['--description']
            options_list = list(itertools.chain(*self.options_dict.items()))
            self.nagios2trac.get_options_and_args(options_list)
        except SystemExit, e:
            self.assertEquals(e.code, 2)
            self.assertTrue('error: please specify a description' in sys.stderr.getvalue())
        else:
            self.fail('Did not raise SystemExit')

    def testNeedsLongoutput(self):
        try:
            del self.options_dict['--longoutput']
            options_list = list(itertools.chain(*self.options_dict.items()))
            self.nagios2trac.get_options_and_args(options_list)
        except SystemExit, e:
            self.assertEquals(e.code, 2)
            self.assertTrue('error: please specify a longoutput' in sys.stderr.getvalue())
        else:
            self.fail('Did not raise SystemExit')

    def testFoundOpenTicketWithSameSummary(self):
        self.nagios2trac.open_ticket_with_same_summary.return_value = [1337]
        self.nagios2trac.main(self.options, self.args)
        self.nagios2trac.open_ticket_with_same_summary.assert_called_with(self.summary_template)
        self.nagios2trac.update_ticket.assert_called_with(1337)

    def testFoundOpenTicketForSameHostWithThresholdExceeded(self):
        service_recovered = False
        self.nagios2trac.open_ticket_with_same_summary.return_value = []
        self.nagios2trac.open_ticket_for_same_host.return_value = [12]
        # ensure that last modified time exceededs threshold
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.get.return_value = [0, 0, datetime.datetime.utcnow() - datetime.timedelta(minutes=self.new_ticket_threshold + 10)]
        self.nagios2trac.main(self.options, self.args)

        self.nagios2trac.create_ticket_if_not_recovered.assert_called_with(self.summary_template, self.description_template, self.trac_owner, service_recovered)

    def testFoundOpenTicketForSameHostWithinThreshold(self):
        service_recovered = False
        self.nagios2trac.open_ticket_with_same_summary.return_value = []
        self.nagios2trac.open_ticket_for_same_host.return_value = [12]
        # Timestamp of now to stay in threshold
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.get.return_value = [0, 0, datetime.datetime.utcnow()]
        self.nagios2trac.main(self.options, self.args)
        self.nagios2trac.open_ticket_for_same_host.assert_called_with(self.options.critical_host)
        # use current time to be within threshold
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.get.assert_called_with(12)

        self.nagios2trac.update_ticket.assert_called_with(12)

    def testFoundNoMatchingOpenTicket(self):
        service_recovered = False
        self.nagios2trac.open_ticket_with_same_summary.return_value = []
        self.nagios2trac.open_ticket_for_same_host.return_value = []
        self.nagios2trac.main(self.options, self.args)
        self.nagios2trac.open_ticket_for_same_host.assert_called_with(self.options.critical_host)
        self.nagios2trac.create_ticket_if_not_recovered.assert_called_with(self.summary_template, self.description_template, self.trac_owner, service_recovered)

    def tearDown(self):
        sys.stderr = self._stderr


if __name__ == '__main__':
    unittest.main()
