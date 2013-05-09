import logging
import socket

class rfc5424Formatter(logging.Formatter):
	"""
		logging.handlers.SysLogHandler just send data to an udp server with the priority field
		We must do the remaining job to be compliant with RFC5424.
		MSGID and STRUCTURED-DATA are not supported
	"""
	def __init__(self, fmt=None, datefmt=None):
		syslogHeader = "1 %%(asctime)s %s %%(processName)s %%(process)s - - " % (socket.gethostname())
		if fmt:	fmt = syslogHeader + fmt
		else:	fmt = syslogHeader + "%(message)s"
		logging.Formatter.__init__( self, fmt, "%Y-%m-%dT%H:%M:%SZ" )
