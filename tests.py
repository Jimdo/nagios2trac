import unittest
from StringIO import StringIO
import sys
import itertools

from mock import Mock


class TestNagios2Trac(unittest.TestCase):

    def setUp(self):
        import nagios2trac
        self.nagios2trac = nagios2trac
        self.options_dict = {'--host-name': 'myhost', '--service-state': 'CRITICAL', '--description': 'myservice running', '--longoutput': 'loooong', '--config': 'nagios2trac.conf.default' }
        # convert dict to flat list
        options_list = list(itertools.chain(*self.options_dict.items()))
        self.options, self.args = self.nagios2trac.get_options_and_args(options_list)
        self.nagios2trac.xmlrpclib = Mock()
        self.nagios2trac.update_ticket = Mock()
        self.nagios2trac.create_ticket = Mock()
        self.nagios2trac.create_ticket_if_not_recovered = Mock()
        self._stderr = sys.stderr
        sys.stderr = StringIO()

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
        summary_template = '[myhost] CRITICAL: myservice running'
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = [1337]
        self.nagios2trac.main(self.options, self.args)
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.assert_called_with("summary=" + summary_template + "&status!=closed&order=id&desc=true")
        self.nagios2trac.update_ticket.assert_called_with(1337)

#    def testFoundOpenTicketForSameHostWithThresholdExceeded(self):
#        summary_template = '[myhost] CRITICAL: myotherservice running'
#        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = []
#        self.nagios2trac.main(self.options, self.args)
#        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = [12]

#    def testFoundOpenTicketForSameHostWithinThreshold(self):
#
    def testFoundNoMatchingOpenTicket(self):
        summary_template = '[myhost] CRITICAL: myservice running'
        comment_template_plain = "{{{ \n[myhost] CRITICAL: myservice running\nloooong\n}}}"
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

        # shouldn't this have been already defined by read_config?
        trac_owner = 'sometracuser'
        service_recovered=False
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = []
        self.nagios2trac.main(self.options, self.args)
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = []
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.assert_called_with("summary^=[myhost]&status!=closed&order=id&desc=true")
        self.nagios2trac.create_ticket_if_not_recovered.assert_called_with(summary_template,description_template,trac_owner,service_recovered)

    def tearDown(self):
        sys.stderr = self._stderr


if __name__ == '__main__':
    unittest.main()