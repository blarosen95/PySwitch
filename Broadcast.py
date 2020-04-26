import socket
import pickle
import os
from ipaddress import IPv4Network

reserved = {'192.168.0.1'}


class Broadcast:
    server_restarts = 0
    connected_hostname = ''
    NETWORK = IPv4Network('192.168.0.0/24')

    def start_broadcast_dhcp_server(self):
        s = socket.socket()
        # Note: This would be port 67.
        port = 12347

        s.bind(('', port))
        print(f'Bound to {port}')

        s.listen(5)

        c, addr = s.accept()
        self.connected_hostname = addr[0]
        c.send(b'welcome')
        packet = c.recv(301)
        if len(packet) != 300:
            c.shutdown(socket.SHUT_RDWR)
            c.close()
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            print(f'Client provided {len(packet)} bytes instead of 300 bytes. Function restarting.')
            self.server_restarts += 1
            if self.server_restarts == 2:
                c.close()
                s.close()
                return
            self.start_broadcast_dhcp_server()
        if self.server_restarts == 2:
            return
        c.close()
        s.close()
        return packet

    def break_packet(self, packet):
        header = [packet[:1], packet[1:2], packet[2:3], packet[3:4]]
        identifier = [packet[4:8]]
        informative = [packet[8:10], packet[10:12]]
        ciaddr = [packet[12:16]]
        yiaddr = [packet[16:20]]
        siaddr = [packet[20:24]]
        giaddr = [packet[24:28]]
        chaddr = [packet[28:34], packet[34:44]]
        sname = [packet[44:108]]
        file = [packet[108:236]]
        vend = [packet[236:240], packet[240:243], packet[243:252], packet[252:258], packet[258:264], packet[264:265],
                packet[265:300]]
        discovered = {"header": header, "identifier": identifier, "informative": informative, "ciaddr": ciaddr,
                      "yiaddr": yiaddr, "siaddr": siaddr, "giaddr": giaddr, "chaddr": chaddr, "sname": sname,
                      "file": file, "vend": vend}
        return discovered
        # return [header, identifier, informative, ciaddr, yiaddr, siaddr, giaddr, chaddr, sname, file, vend]

    def get_next_available_host(self):
        network_iterator = (h for h in self.NETWORK.hosts() if str(h) not in reserved)
        next_host = next(network_iterator)
        reserved.add(next_host.exploded)
        return next_host.packed

    def offer(self, discover_pickled):
        discovered = pickle.load(open(discover_pickled, "rb"))
        header = [b'\x02', b'\x01', b'\x06', b'\x00']
        identifier = discovered.get('identifier')
        informative = [b'\x00\x00', b'\x00\x00']
        ciaddr = discovered.get('ciaddr')
        yiaddr = [self.get_next_available_host()]
        siaddr = [b'\xC0\xA8\x00\x01']
        raddr = [b'\x00\x00\x00\x00']
        chaddr = discovered.get('chaddr')
        sname = [b'\x00' * 64]
        file = [b'\x00' * 128]
        vend = [b'\x63\x82\x53\x63', b'\x35\x01\x02', b'\x01\x04\xFF\xFF\xFF\x00', b'\x3A\x04\x00\x00\x07\x08',
                b'\x3B\x04\x00\x00\x0C\x4E', b'\x33\x04\x00\x00\x0E\x10', b'\x36\x04\xC0\xA8\x00\x01', b'\xFF',
                b'\x00' * 26]

        offer_packet = {"header": header, "identifier": identifier, "informative": informative, "ciaddr": ciaddr,
                        "yiaddr": yiaddr, "siaddr": siaddr, "raddr": raddr, "chaddr": chaddr, "sname": sname,
                        "file": file, "vend": vend}
        offer_pickle = pickle.dumps(offer_packet)
        addr = self.connected_hostname
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, 12348))
        s.send(offer_pickle)
        s.close()


test = Broadcast()

while True:
    packet = test.start_broadcast_dhcp_server()
    discovery = test.break_packet(packet)
    filename_bytes = discovery.get("identifier")
    filename = ''
    for byte in filename_bytes:
        filename += str(byte)
    pickle.dump(discovery, open(f'{filename}.PICKLE', "wb"))
    test.offer(f'{filename}.PICKLE')
    print(f'We\'ve assigned {len(reserved)} addresses.\nThey are: {reserved}')
    os.remove(f'{filename}.PICKLE')
