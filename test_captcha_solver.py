import unittest
# simple_solver(https://github.com/ptigas/simple-CAPTCHA-solver)
from captcha_decoder import decoder
from captcha import captcha_to_string
from PIL import Image

path2expected = {
    'capcha_07-12 00:33:15.png': 'CTCH',
    'capcha_07-12 00:28:33.png': 'CP8F',
    'capcha_07-12 00:26:43.png': 'CWJB',
    'capcha_07-11 23:34:23.png': 'CQ3R'
}


def format_result(expected, actual):
    result = "True" if expected == actual else "False"
    return f"{result} {expected} {actual}"


class TestCapchaSolvers(unittest.TestCase):

    def test_simple_solver(self):
        solver = decoder
        print("\n".join(format_result(answer, solver(path)) for path,
                        answer in path2expected.items()))

    def test_solver(self):
        def solver(path):
            return captcha_to_string(Image.open(path))
        print("\n".join(format_result(expected, solver(path)) for path,
                        expected in path2expected.items()))


if __name__ == '__main__':
    unittest.main()
