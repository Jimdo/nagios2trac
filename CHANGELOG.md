# 0.2.1
  * BUGFIX: do not create a new ticket if a service or host recovers
  * make it possible to provide newlines in parameters with \n (this is useful for multiline longoutput)

# 0.2
 * new param: new_ticket_threshold (minutes)

  if anopen ticket with a different description for one host is found 
  only post to it if last edit is time is < new_ticket_threshold minutes.
  otherwise create a new ticket

# 0.1.1

  * initial release