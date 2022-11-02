import unittest

import time
from elastic.core.common.profile_migration_speed import profile_migration_speed


class TestProfileMigrationSpeed(unittest.TestCase):
    def test_profile_migration_speed(self):
        """
            Profiled migration speed should be nonzero.
        """
        self.assertLess(0, profile_migration_speed("../../../examples"))

    def test_function_runtime(self):
        """
            Function should complete in less than 1 second.
        """
        start = time.time()
        profile_migration_speed("../../../examples")
        duration = time.time() - start
        self.assertGreaterEqual(1.1, duration)  # Allow some leeway


if __name__ == '__main__':
    unittest.main()
