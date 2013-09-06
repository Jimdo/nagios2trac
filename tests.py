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
        self.critical_host = 'myhost'
        self.description = 'some service'

    def testOpenTicketWithSameSummaryTrue(self):
        self.nagios2trac.open_ticket_for_same_host = Mock()
        self.nagios2trac.open_ticket_for_same_host.return_value = [1337]
        self.nagios2trac.SERVER.ticket.get.return_value = [0, 0, datetime.datetime.utcnow(), {'summary': 'some service'}]
        result = self.nagios2trac.open_ticket_with_same_summary(self.critical_host, self.description)
        self.nagios2trac.SERVER.ticket.get.assert_called_with(1337)
        self.assertEqual(result, [1337])

    def testOpenTicketWithSameSummaryNoHostMatch(self):
        self.nagios2trac.open_ticket_for_same_host = Mock()
        self.nagios2trac.open_ticket_for_same_host.return_value = None
        result = self.nagios2trac.open_ticket_with_same_summary(self.critical_host, self.description)
        self.assertEqual(result, None)

    def testOpenTicketWithSameSummaryNoDescriptionMatch(self):
        self.nagios2trac.open_ticket_for_same_host = Mock()
        self.nagios2trac.open_ticket_for_same_host.return_value = [1337]
        self.nagios2trac.SERVER.ticket.get.return_value = [0, 0, datetime.datetime.utcnow(), {'summary': 'bla'}]
        result = self.nagios2trac.open_ticket_with_same_summary(self.critical_host, self.description)
        self.nagios2trac.SERVER.ticket.get.assert_called_with(1337)
        self.assertEqual(result, None)

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
        self.comment_template = self.comment_template_plain.replace('\\n', '\n')
        self.description_template = """=== Incident ===
  * What is broken?
""" + self.comment_template + """
  * add some
  * more content
  * here
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
        self.nagios2trac.open_ticket_with_same_summary.assert_called_with(self.options.critical_host, self.options.description)
        self.nagios2trac.update_ticket.assert_called_with(1337, self.comment_template)

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

        self.nagios2trac.update_ticket.assert_called_with(12, self.comment_template)

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
