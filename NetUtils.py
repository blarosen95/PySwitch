from datetime import datetime
from random import shuffle
from array import array


def create_transaction_id():
    options = []

    for i in range(0, 9):
        options.append(i)
    for i in range(11, 32):
        options.append(i)
    for i in range(127, 256):
        options.append(i)

    xid_array = []
    for i in range(0, 4):
        shuffle(options)
        xid_array.append(options[0])

    return array('B', xid_array).tobytes()

def create_dhcp_packet(transid, mac, client, options):
    start_time = datetime.now()
    # Start of DHCP Header
    op = b'\x01'
    htype = b'\x01'
    hlen = len(mac).to_bytes(1, 'big')
    hops = b'\x00'
    header = [op, htype, hlen, hops]
    # End of DHCP Header
    # Start of Identifier
    xid = transid
    identifier = [transid]
    # End of Identifier
    # Start of Informative
    time_here = datetime.now()
    seconds = (time_here - start_time).seconds.to_bytes(2, 'big')
    flags = b'\x00\x00'
    informative = [seconds, flags]
    # End of Informative
    # Start of CIADDR
    client_ip_address = client.ip_address.packed
    ciaddr = [client_ip_address]
    # End of CIADDR
    # Start of YIADDR
    my_ip_address = client.ip_address.packed
    yiaddr = [my_ip_address]
    # End of YIADDR
    # Start of SIADDR
    server_ip_address = client.ip_address.packed
    siaddr = [server_ip_address]
    # End of SIADDR
    # Start of GIADDR
    gateway_ip_address = client.ip_address.packed
    giaddr = [gateway_ip_address]
    # End of GIADDR
    # Start of CHADDR
    # client_hardware_address = self.mac_address.replace(':', '', 5)
    client_hardware_address = mac
    chaddr_padding = 16 - len(client_hardware_address)
    chaddr = [client_hardware_address, b'\x00' * chaddr_padding]
    # End of CHADDR
    # Start of SNAME
    server_host_name = b'\x00' * 64
    sname = [server_host_name]
    # End of SNAME
    # Start of FILE
    boot_filename = b'\x00' * 128
    file = [boot_filename]
    # End of FILE
    # Start of VEND section (64 bytes)
    magic_cookie = b'\x63\x82\x53\x63'
    dhcp_type = b'\x53\x01' + options[0]
    client_identifier = b'\x3D\x07\x01' + options[1]
    # requested_ip = f'3204{self.ip_address.packed}'
    requested_ip = b'\x32\x04' + options[2]
    parameter_requests = b'\x37\x04\x01\x03\x06\x2a'
    end = b'\xff'
    vend = [magic_cookie, dhcp_type, client_identifier, requested_ip, parameter_requests, end]
    vend_bytes = 0
    for item in vend:
        vend_bytes += len(item)
    vend_padding = b'\x00' * (64 - vend_bytes)
    vend.append(vend_padding)
    # End of VEND section (64 bytes)
    dhcp_packet = [header, identifier, informative, ciaddr, yiaddr, siaddr, giaddr, chaddr, sname, file, vend]
    return dhcp_packet
