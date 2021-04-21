# encoding = utf - 8
# NDN Simulation: Aishan Li

from common import CONTENT_STORE_SIZE, PACKET_LIFETIME, count_prefix_length
from collections import OrderedDict


class Packet:
    def __init__(self, src, dst, lifetime=PACKET_LIFETIME):
        self.src = src  # /edu.umich/ECE/1
        self.dst = dst  # /edu.uchicago/CS/2
        self.text = ""
        self.lifetime = lifetime


class InterestPacket(Packet):
    def __init__(self, src, dst):
        super().__init__(src, dst)


class DataPacket(Packet):
    def __init__(self, src, dst, text):
        super().__init__(src, dst)
        self.text = text


class ContentStore(OrderedDict):
    def __init__(self):
        super().__init__()

    def get(self, key: int) -> int:
        if key not in self:
            return -1
        self.move_to_end(key)
        return self[key]

    def add(self, key: int, value: str) -> None:
        if key in self:
            self[key] = value
            self.move_to_end(key)
        if len(self) == CONTENT_STORE_SIZE:
            self._delete_one()
        self[key] = value

    def _delete_one(self):
        return self.popitem(last=False)


class PendingInterestTable(list):
    def __init__(self):
        super().__init__()
        self.pointer = 0

    def remove_by(self, src, dst):
        for i, entry in enumerate(self):
            if i >= self.pointer:
                break
            if entry.src == src and entry.dst == dst:
                self.remove(entry)
                if self.pointer > 0:
                    self.pointer -= 1
                return

    def get_one(self):
        if len(self) > 0:
            self.pointer += 1
            return self[self.pointer - 1]

    def has_new(self):
        return 0 <= self.pointer < len(self)


class Vertex(object):
    def __init__(self, _name, _text="", cache_size=CONTENT_STORE_SIZE):
        self.name = _name  # /edu.umich/ECE
        self.text = _text

        self._delay_time = 0
        self._sending_pkt = None

        # Forwarding Information Base (FIB):
        # maintains next- hop(s) and other information
        # for each reachable destination name prefix.
        self.FIB = {}  # next-hop key -> vertex

        # Pending Interest Table(PIT):
        # maintains an entry for each incoming Interest
        # packet until its corresponding Data packet arrives
        # or the entry lifetime expires
        self.PIT = PendingInterestTable()  # List of InterestPacket

        # content store: NDN router caches a copy of Data packet
        # passing through them (based on the local caching policy)
        # in the content store, until they get replaced by the
        # new content (because of finite cache size)
        self.CS = ContentStore()  # src key -> text
        if self.text:
            # If self is an endpoint, then store the content in CS
            self.CS.add(self.name, self.text)

        self.packet_buffer = []  # packets to be forwarded

    def generate_interest_pkt(self, dst):
        self.PIT.append(InterestPacket(self.name, dst))

    def get_next_hop(self, dst):
        _next_ver, _max_count = None, 0
        for _next_name in self.FIB.keys():
            _count = count_prefix_length(_next_name, dst)
            if _count > _max_count:
                _next_ver, _max_count = self.FIB[_next_name], _count
        return _next_ver

    def forward(self, cur) -> int:
        """
        if forward sth: return 1
        if forward nothing: return 0
        """
        # if not self.packet_buffer:
        #     if len(self.PIT) == 0:
        #         return 0
        #     else:
        #         self.packet_buffer.append(self.PIT[0])
        #         _tmp = self.PIT.pop(0)
        #         self.PIT.append(_tmp)

        # cur = self.packet_buffer.pop(0)
        _next = self.get_next_hop(cur.dst)
        if type(cur) == DataPacket:
            # add this data packet into local cache
            self.CS.add(cur.src, cur.text)
            # forward this data packet to next hop
            if cur.dst != self.name:
                _next.packet_buffer.append(cur)
            self.PIT.remove_by(cur.dst, cur.src)
        elif type(cur) == InterestPacket:
            if cur.dst in self.CS:
                # found in local cache (CS)
                fabricated_dataPkt = DataPacket(cur.dst, cur.src, self.CS.get(cur.dst))
                reversed_next = self.get_next_hop(cur.src)
                reversed_next.packet_buffer.append(fabricated_dataPkt)
                self.PIT.remove_by(cur.dst, cur.src)
            else:
                # not found in local cache (CS)
                _next.packet_buffer.append(cur)

        return 1

    def check_PIT_lifetime(self):
        # decrease the life time of all entries in PIT
        for I_pkt in self.PIT:
            I_pkt.lifetime -= 1

        # drop the expired entries in PIT
        drop_count = 0
        for i in range(len(self.PIT) - 1, -1, -1):
            if self.PIT[i].lifetime <= 0:
                self.PIT.pop(i)
                drop_count += 1

        return drop_count

    def run_step(self):
        """
            For simulation: run one step
        """
        if self._delay_time > 0:
            self._delay_time -= 1
            return 0, self.check_PIT_lifetime()

        if self._sending_pkt:
            self.forward(self._sending_pkt)
            self._sending_pkt = None
            return 1, self.check_PIT_lifetime()

        if not self.packet_buffer and self.PIT.has_new():
            self.packet_buffer.append(self.PIT.get_one())

        if len(self.packet_buffer) > 0:
            self._sending_pkt = self.packet_buffer.pop(0)
            self._delay_time += len(self._sending_pkt.text)

        return 0, self.check_PIT_lifetime()

    def run(self, times=1):
        """
        For simulation: run several step
        """
        total_status, total_drops = 0, 0

        for i in range(times):
            _status, _drops = self.run_step()
            total_status += _status
            total_drops += _drops

        return total_status, total_drops







