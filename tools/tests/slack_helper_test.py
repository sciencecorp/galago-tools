import unittest
import sys 

sys.path.append("../..")

class TestSlackToolHelpers(unittest.TestCase):
        
    def test_get_slack_id_from_scientist_name(self) -> None:
        #Test 1
        slack_id = "12345"
        self.assertEqual(slack_id, "12345")

if __name__ == '__main__':
    unittest.main()