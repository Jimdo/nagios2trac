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


Installation
============
The easiest way to install nagios2trac and its dependencies:
```
$ pip install nagios2trac
```

Alternatively install it from source
```
$ git clone git@github.com:Jimdo/nagios2trac.git
$ cd nagios2trac/
$ python setup.py install
```

Usage
=====
Define these notification commands in nagios

 * service check:

        nagios2trac.py --service-state "$SERVICESTATE$ $NOTIFICATIONTYPE$" --host-name "$HOSTNAME$" --description "$SERVICEDESC$" --longoutput "$SERVICEOUTPUT$"

 * host check:

        nagios2trac.py --service-state "$HOSTSTATE$ $NOTIFICATIONTYPE$" --host-name "$HOSTNAME$" --description "" --longoutput ""
