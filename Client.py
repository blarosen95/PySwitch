import ipaddress
import pickle
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
        transaction = NetUtils.create_transaction_id()
        opts = [b'\x01', self.mac_bytecode, self.ip_address.packed]
        dhcp_arr = NetUtils.create_dhcp_packet(transaction, self.mac_bytecode, self.ip_address, opts)
        discover = b''
        for arr in dhcp_arr:
            for item in arr:
                discover += item
        return discover

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
        packet = c.recv(595)
        if len(packet) != 594:
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
        return pickle.loads(packet)

    def broadcast_socket(self, packet):
        # Note, as this is being virtualized and mocked up, I'm using a VM named 'BROADCAST' for the "broadcast address"
        # This VM will run a server socket that behaves as much like a real broadcast as possible, in the sense that all
        # Other VMs running this project will listen to it.
        addr = socket.gethostbyname('BROADCAST')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, 12347))
        s.send(packet)
        print('Sent discovery packet!')
        s.shutdown(socket.SHUT_RDWR)
        print('Socket shut!')

    def dhcp_procedure(self):
        # Instantiate DHCPDISCOVER packet
        discover = self.dhcp_discover()
        # "Broadcast" this packet to the broadcast VM's socket
        self.broadcast_socket(discover)
        print('Exited from broadcasting discovery.')
        # Await "unicast" reply from switch
        offer = self.start_client_dhcp_server()
        print(offer.get('yiaddr'))
        # TODO: if offer packet is good, then do the following:
        # Instantiate DHCPREQUEST packet
        request = ''


tester = Client('00:0A:8A:1C:08:DA', b'\x00\x0A\x8A\x1C\x08\xDA')

tester.dhcp_procedure()
