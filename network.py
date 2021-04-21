# encoding = utf - 8
# NDN Simulation: Aishan Li

from Definition import Vertex
from common import MAX_STEPS
from collections import defaultdict


class NdnNetwork:
    def __init__(self):
        self.vertices = []
        self.endpoints = []

        self.total_packet_count = 0
        self.packet_count = defaultdict(int)

    def load_network_structure(self, config_path):
        vertex_flag = False
        edge_flag = False
        with open(config_path, mode='r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line == '[Vertices]\n':
                    vertex_flag = True
                    continue

                if line == '[Edges]\n':
                    edge_flag = True
                    vertex_flag = False
                    continue

                if line != '\n' and vertex_flag:
                    line_split = line.split()
                    if len(line_split) == 2:
                        _ver = Vertex(line_split[1])
                    elif len(line_split) == 3:
                        _ver = Vertex(line_split[1], line_split[2])
                        self.endpoints.append(_ver)
                    self.vertices.append(_ver)
                    continue

                if line != '\n' and edge_flag:
                    line_split = line.split()
                    ver1 = self.vertices[int(line_split[0])]
                    ver2 = self.vertices[int(line_split[1])]
                    ver1.FIB[ver2.name] = ver2
                    ver2.FIB[ver1.name] = ver1
                    continue

    def finish(self):
        for ver in self.vertices:
            if len(ver.PIT) > 0 or len(ver.packet_buffer) > 0:
                return False
        return True

    def statistics(self):
        # print('========================================\n')
        for ver in self.vertices:
            self.packet_count[ver.name] += len(ver.packet_buffer)
            self.total_packet_count += len(ver.packet_buffer)
        #     print('--------------------------------\n')
        #     print(ver.name + ':\n')
        #     print('PIT: ')
        #     print(ver.PIT)
        #
        #     print('CS: ')
        #     print(ver.CS)
        #
        #     print('Buffer: ')
        #     print(ver.packet_buffer)
        #     print('--------------------------------\n')
        # print('========================================\n')

    def simulation(self, forwards_one_step: int, initial_pkt_number: int):
        for _end in self.endpoints:
            # Automatically generate "initial_pkt_number" pkts in PIT
            for _other in self.endpoints:
                if _other != _end:
                    for _ in range(initial_pkt_number):
                        _end.generate_interest_pkt(_other.name)

        total_drop_count = 0
        for step_count in range(MAX_STEPS):
            total_status = 0
            for ver in self.vertices:
                _status, _drops = ver.run_step()
                total_drop_count += _drops
                total_status += _status

            self.statistics()

            if self.finish():
                break

        print('Total packet loss: ', total_drop_count)
        print('Number of steps: ', step_count)
        print('Avg load of the whole network: ', self.total_packet_count/step_count)
        print()
        print('Avg load of each vertex:')
        for ver in self.vertices:
            print(ver.name, ' ' * (25 - len(ver.name)), self.packet_count[ver.name]/step_count)
        # print(total_drop_count, step_count)


if __name__ == '__main__':
    network = NdnNetwork()
    network.load_network_structure('example_construction')
    network.simulation(5, 7)






