import sys
sys.path.append('.')


def sum(a, b):
    return a + b

def test_sum1(mocker):
    mocker.patch(__name__ + ".sum", return_value=9)
    assert sum(2, 3) == 9