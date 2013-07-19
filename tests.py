import unittest
from StringIO import StringIO
import sys
import itertools

from mock import Mock


class TestNagios2Trac(unittest.TestCase):

    def setUp(self):
        import nagios2trac
        self.nagios2trac = nagios2trac
        self.options_dict = {'--host-name': 'myhost', '--service-state': 'CRITICAL', '--description': 'myservice running', '--longoutput': 'loooong'}
        # convert dict to flat list
        options_list = list(itertools.chain(*self.options_dict.items()))
        self.options, self.args = self.nagios2trac.get_options_and_args(options_list)
        self.nagios2trac.read_config = Mock()
        self.nagios2trac.read_config.return_value = [1, 2, 3, 4, 5]
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
        description_template = 'dummy'
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = []
        self.nagios2trac.main(self.options, self.args)
#        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.assert_called_with("summary=" + summary_template + "&status!=closed&order=id&desc=true")
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = []
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.assert_called_with("summary^=[myhost]&status!=closed&order=id&desc=true")
        self.nagios2trac.create_ticket_if_not_recovered.assert_called_with(summary_template,description_template,trac_owner,service_recovered)
#        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.assert_called_with("summary^=[" + options.critical_host + "]&status!=closed&order=id&desc=true")
#        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = []
#        self.nagios1trac.xmlrpclib.ServerProxy().ticket.query.assert_called_with("summary=" + summary_template + "&status!=closed&order=id&desc=true")

    def tearDown(self):
        sys.stderr = self._stderr


if __name__ == '__main__':
    unittest.main()
