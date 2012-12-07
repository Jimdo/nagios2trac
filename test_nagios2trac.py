from nagios2trac import *
from mock import Mock

def test_creation():
    host_name = 'somehost.somedomain'
    description = 'disk free'
    service_state = 'CRITICAL'    
    
    trac_query = {}
    trac_query['summary^=[somehost.somedomain]'] = 22665
    trac_api = Mock()
    trac_api.find_by_host.return_value = None

    create_tickets(nagios_input, trac_api)

    assert 'ticket "[somehost.somedomain] disk free" created' == trac_api.last_log_message

