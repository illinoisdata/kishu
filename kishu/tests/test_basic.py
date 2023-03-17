# -*- coding: utf-8 -*-

from .context import kishu

import unittest


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_version(self):
        assert kishu.version() == '0.1.0'


if __name__ == '__main__':
    unittest.main()
