import unittest
from StringIO import StringIO
import sys
import itertools

from mock import Mock


class TestNagios2Trac(unittest.TestCase):

    def setUp(self):
        import nagios2trac
        self.nagios2trac = nagios2trac
        self.options_dict = {'--host-name': 'deine', '--service-state': 'CRITICAL', '--description': 'mudda running', '--longoutput': 'loooong'}
        # convert dict to flat list
        options_list = list(itertools.chain(*self.options_dict.items()))
        self.options, self.args = self.nagios2trac.get_options_and_args(options_list)
        self.nagios2trac.read_config = Mock()
        self.nagios2trac.read_config.return_value = [1, 2, 3, 4, 5]
        self.nagios2trac.xmlrpclib = Mock()
        self.nagios2trac.update_ticket = Mock()
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
        summary_template = '[deine] CRITICAL: mudda running'
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.return_value = [1337]
        self.nagios2trac.main(self.options, self.args)
        self.nagios2trac.xmlrpclib.ServerProxy().ticket.query.assert_called_with("summary=" + summary_template + "&status!=closed")
        self.nagios2trac.update_ticket.assert_called_with(1337)

    def tearDown(self):
        sys.stderr = self._stderr


if __name__ == '__main__':
    unittest.main()
