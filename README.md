[![Build Status](https://travis-ci.org/Jimdo/nagios2trac.png?branch=master)](https://travis-ci.org/Jimdo/nagios2trac)

nagios2trac
===========

Let Nagios create or comment TRAC tickets for you


Privileges needed for Trac user
==============================
* TICKET\_MODIFY
* TICKET\_CREATE
* TICKET\_VIEW
* XML\_RPC


Usage
=====
Define these notification commands
* service check:

        ./nagios2trac.py --service-state "$SERVICESTATE$ $NOTIFICATIONTYPE$" --host-name "$HOSTNAME$" --description "$SERVICEDESC$" --longoutput "$SERVICEOUTPUT$"
* host check:

        ./nagios2trac.py --service-state "$HOSTSTATE$ $NOTIFICATIONTYPE$" --host-name "$HOSTNAME$" --description "" --longoutput ""
