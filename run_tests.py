#!/usr/bin/env python
"""
运行 Werewolf Game 的单元测试
"""

import sys
import unittest

if __name__ == "__main__":
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    start_dir = "tests"
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回适当的退出码
    sys.exit(0 if result.wasSuccessful() else 1)
