import struct
from typing import Dict, List

Occurrences = Dict[str, List[int]]
meanOccs = Dict[str, float]


def serialize_occurrences(to_serialize: Occurrences) -> bytes:
	print('serialize_occurrences')
	island_count = len(to_serialize)
	islands = [struct.pack(f"ii{len(v)}i", int(k), len(v), *v) for k, v in to_serialize.items()]
	return struct.pack("i", island_count) + b''.join(islands)


def deserialize_occurrences(to_deserialize: bytes) -> Occurrences:
	print('deserialize_occurrences')
	res = {}
	island_count, = struct.unpack('i', to_deserialize[:4])
	cursor = 4
	for _ in range(island_count):
		format_ = "ii"
		read_size = struct.calcsize(format_)
		island_size, sample_count = struct.unpack(format_, to_deserialize[cursor:cursor+read_size])
		cursor += read_size
		format_ = f"{sample_count}i"
		read_size = struct.calcsize(format_)
		assert island_size not in res, f"Key {island_size} found more than once!"
		res[island_size] = list(struct.unpack(format_, to_deserialize[cursor:cursor+read_size]))
		cursor += read_size
	return res
