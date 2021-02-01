import pytest
from src.suffix_trees.STree import starts_with, STree


def test_lcs():
    a = [
        [1, 2, 5, 3, 5, 4, 1], [1, 2, 5, 3, 5, 4, 14, 9, 11], [1, 2, 5, 1, 2, 5, 3, 5, 4, 1, 2, 5, 3, 5, 4],
        [1, 2, 5, 3, 5, 4, 1, 1, 1, 1],
        [1, 1, 1, 2, 2, 2, 5, 5, 5, 3, 3, 5, 5, 5, 4, 4, 1, 1, 1, 1, 1, 2, 5, 3, 5, 4, 1]]
    st = STree(a)
    assert st.lcs() == [1, 2, 5, 3, 5, 4]


def test_missing():
    text = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    stree = STree(text)
    assert stree.find((4, 3, 2)) == -1
    assert stree.find((9, 9, 9)) == -1
    assert stree.find(tuple(text) + (20,)) == -1


def test_find():
    data = list(range(1, 9)) + list(range(1, 3))
    st = STree(data)
    assert st.find((1, 2, 3)) == 0
    assert st.find_all((1, 2)) == {0, 8}


@pytest.mark.parametrize("is_tuple", (True, False))
@pytest.mark.parametrize("to_check,prefix,expected", (
        ([1, 2, 3, 4], [1, 2, 3], True),
        ([1, 2, 3, 4], [1, 2], True),
        ([1, 2, 3, 4], [1], True),
        ([1, 2, 3, 4], [], True),
        ([1, 2, 3, 4], [2], False),
        ([1, 2, 3, 4], [4, 3, 2, 1], False)
))
def test_starts_with(is_tuple: bool, to_check, prefix, expected):
    if is_tuple:
        prefix = tuple(prefix)
    assert expected == starts_with(to_check, prefix)
