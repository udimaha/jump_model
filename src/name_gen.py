class NameGenerator:
    RANGE_START = 'A'
    RANGE_END = 'B'

    def __init__(self):
        self._next_name = str(self.RANGE_START)

    def next(self) -> str:
        name = str(self._next_name)
        if self._next_name[-1] < 'Z':
            if len(self._next_name) == 1:
                self._next_name = chr(ord(self._next_name[0]) + 1)
            else:
                self._next_name = self._next_name[:-1] + chr(ord(self._next_name[-1]) + 1)
        else:
            self._next_name += self.RANGE_START
        return name


def test_name_generator():
    name_gen = NameGenerator()
    all_names = set()
    for i in range(10000):
        next_ = name_gen.next()
        assert next_ not in all_names, f"{next_} appears more than once!"
        all_names.add(next_)
