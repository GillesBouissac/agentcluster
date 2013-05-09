from agentcluster.exception import ClusterException
import logging

logger = logging.getLogger('agentcluster.transport')

udp = None
udp6 = None
unix = None
try:
    from pysnmp.carrier.asynsock.dgram import udp
except ImportError:
    pass;
try:
    from pysnmp.carrier.asynsock.dgram import udp6
except ImportError:
    pass;
try:
    from pysnmp.carrier.asynsock.dgram import unix
except ImportError:
    pass;

__all__ = ["SocketHelper"]


class TransportHelperBase:
    idx         = 0;
    domain      = None;
    pclass      = None;
    def parseAddress (self, params):
        pass;

class TransportHelperUdp(TransportHelperBase):
    """ Provides tools to initialize IPV4 UDP transport """
    def __init__ (self):
        if udp:
            self.domain      = udp.domainName;
            self.pclass      = udp.UdpTransport;

    def parseAddress (self, params):
        f = lambda h,p=161 : (h, int(p) )
        try:
            return f( *params.split(':') )
        except:
            msg = 'improper IPv4/UDP endpoint %s' % params;
            logger.error ( msg );
            raise ClusterException(msg);

class TransportHelperUdp6(TransportHelperBase):
    """ Provides tools to initialize IPV4 UDP transport """
    def __init__ (self):
        if udp6:
            self.domain      = udp6.domainName;
            self.pclass      = udp6.Udp6Transport;

    def parseAddress (self, params):
        if params.find(']:') != -1 and params[0] == '[':
            h, p = params.split(']:')
            try:
                h, p = h[1:], int(p)
            except:
                msg = 'improper IPv6/UDP endpoint %s' % params;
                logger.error ( msg );
                raise ClusterException(msg);
        elif params[0] == '[' and params[-1] == ']':
            h, p = params[1:-1], 161
        else:
            h, p = params, 161
        return (h, p);

class TransportHelperUnix(TransportHelperBase):
    """ Provides tools to initialize IPV4 UDP transport """
    def __init__ (self):
        if unix:
            self.domain      = unix.domainName;
            self.pclass      = unix.UnixTransport;

    def parseAddress (self, params):
        return params;

class SocketHelper:
    protoHelpers = {
        "udp":  TransportHelperUdp(),
        "udp6": TransportHelperUdp6(),
        "unix": TransportHelperUnix()
    };

    def openSocket(self, protocol, params):

        if not protocol in self.protoHelpers:
            msg = 'Transport protocol %s not supported, supported transport protocols are %s. Aborting' % (protocol,self.protoHelpers.keys())
            logger.error ( msg );
            raise ClusterException(msg);
        protoHelper = self.protoHelpers[protocol]

        # Increment the transport domain idx to have different values for each (in fact we don't care)
        protoHelper.idx += 1 ;
        domain = protoHelper.domain + (protoHelper.idx,);
        address = protoHelper.parseAddress(params);
        transport = protoHelper.pclass();

        logger.debug ( 'Binding %s on domain %s with attributes: %s', protoHelper.pclass.__name__, domain, str(address) );
        socket = transport.openServerMode( address );
        return ( domain, socket );


