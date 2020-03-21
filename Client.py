import ipaddress
from datetime import datetime
import socket
import NetUtils


class Client:
    mac_address = ''
    mac_bytecode = ''
    ip_address = ''
    packed_ip_address = ''
    subnet_mask = ''
    gateway = ''
    dns_primary = ''
    dns_secondary = ''
    server_restarts = 0

    def __init__(self, mac, mac_byte):
        self.mac_address = mac
        self.mac_bytecode = mac_byte
        self.ip_address = ipaddress.ip_address('0.0.0.0')
        self.gateway = ipaddress.ip_address('255.255.255.255')
        # TODO: Call the client-side DHCP code and (re)assign the correct values

    def dhcp_discover(self):
        start_time = datetime.now()
        # Start of DHCP Header
        op = b'\x01'
        htype = b'\x01'
        hlen = len(self.mac_bytecode).to_bytes(1, 'big')
        hops = b'\x00'
        header = [op, htype, hlen, hops]
        # End of DHCP Header
        # Start of Identifier
        xid = NetUtils.create_transaction_id()
        identifier = [xid]
        # End of Identifier
        # Start of Informative
        time_here = datetime.now()
        seconds = (time_here - start_time).seconds.to_bytes(2, 'big')
        flags = b'\x00\x00'
        informative = [seconds, flags]
        # End of Informative
        # Start of CIADDR
        client_ip_address = self.ip_address.packed
        ciaddr = [client_ip_address]
        # End of CIADDR
        # Start of YIADDR
        my_ip_address = self.ip_address.packed
        yiaddr = [my_ip_address]
        # End of YIADDR
        # Start of SIADDR
        server_ip_address = self.ip_address.packed
        siaddr = [server_ip_address]
        # End of SIADDR
        # Start of GIADDR
        gateway_ip_address = self.ip_address.packed
        giaddr = [gateway_ip_address]
        # End of GIADDR
        # Start of CHADDR
        # client_hardware_address = self.mac_address.replace(':', '', 5)
        client_hardware_address = self.mac_bytecode
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
        dhcp_type = b'\x53\x01\x01'
        client_identifier = b'\x3D\x07\x01' + client_hardware_address
        # requested_ip = f'3204{self.ip_address.packed}'
        requested_ip = b'\x32\x04' + self.ip_address.packed
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

    def start_client_dhcp_server(self):
        s = socket.socket()
        print("Socket successfully created")
        # Note: This would be port 68. However, this is all being mocked up. In reality, I wouldn't need to write
        # client-side code for a switch to work, as the DHCP process is done by the OS automatically; I just felt that
        # it would be best practice to mock up how the whole process looks as I haven't got any hardware to use for a
        # more realistic prototype.
        port = 12348

        s.bind(('', port))
        print(f'Bound to {port}')

        s.listen(5)
        print('socket listening')

        c, addr = s.accept()
        c.send(b'welcome')
        packet = c.recv(301)
        if len(packet) != 300:
            c.close()
            s.close()
            print(f'Client provided {len(packet)} bytes instead of 300 bytes. Function restarting.')
            self.server_restarts += 1
            if self.server_restarts == 2:
                c.close()
                s.close()
                return
            tester.start_client_dhcp_server()
        if self.server_restarts == 2:
            return
        print(f"Received {len(packet)} bytes. Closing connection.")
        c.close()
        s.close()
        return packet

    def broadcast_socket(self, packet):
        # Note, as this is being virtualized and mocked up, I'm using a VM named 'BROADCAST' for the "broadcast address"
        # This VM will run a server socket that behaves as much like a real broadcast as possible, in the sense that all
        # Other VMs running this project will listen to it.
        socky = socket.gethostbyname('BROADCAST')
        print(socky)


    def dhcp_procedure(self):
        # Instantiate DHCPDISCOVER packet
        discover = self.dhcp_discover()
        # "Broadcast" this packet to the broadcast VM's socket
        self.broadcast_socket(discover)
        # Await "unicast" reply from switch
        offer = self.start_client_dhcp_server()
        # TODO: if offer packet is good, then do the following:
        # Instantiate DHCPREQUEST packet
        request = ''

tester = Client('00:0A:8A:1C:08:DA', b'\x00\x0A\x8A\x1C\x08\xDA')
discoverer = tester.dhcp_discover()

tester.start_client_dhcp_server()

tester.broadcast_socket(discoverer)
