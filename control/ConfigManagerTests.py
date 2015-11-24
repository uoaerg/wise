import unittest
import ConfigManager

""" Unit tests for ConfigManager """


class StoreRetreiveCfg(unittest.TestCase):
    sample_cfg = {'a': 1,
                  'b': 2,
                  'c': 3, }
    sample_wrong_cfg = {'a': 1,
                        'b': 2,
                        'c': 3,
                        'd': 4}
    single_key = 'X'
    single_value = 10
    key_list = ['a', 'b', 'c']
    value_list = [1, 2, 3]

    def testStoreRetreiveCfg(self):
        cm = ConfigManager.ConfigManager('testStoreRetreiveCfg.JSON')
        cm.store_cfg_dict(self.sample_cfg)
        ret_cfg = cm.get_cfg_dict()
        for key in self.sample_cfg:
            self.assertEqual(self.sample_cfg[key], ret_cfg[key])

    def testSetGet(self):
        cm = ConfigManager.ConfigManager('testSetGet.JSON')
        cm.set_key_value(self.single_key, self.single_value)
        saved_value = cm.get_key_value(self.single_key)
        self.assertEqual(self.single_value, saved_value)

    def testSetGetLists(self):
        cm = ConfigManager.ConfigManager('testSetGetLists.JSON')
        cm.set_key_values(self.key_list, self.value_list)
        saved_values = cm.get_key_values(self.key_list)
        self.assertEqual(len(saved_values), len(self.value_list))
        for index in range(0, len(saved_values)):
            self.assertEqual(self.value_list[index], saved_values[index])

    def testCompareDicts(self):
        cm = ConfigManager.ConfigManager('testCompareDicts.JSON')
        cm.set_key_values(self.key_list, self.value_list)
        saved_values = cm.get_key_values(self.key_list)
        new_dict = dict()
        for index in range(0, len(self.key_list)):
            new_dict[self.key_list[index]] = saved_values[index]
        self.assertEqual(cm.compare_cfg_dict(new_dict), True)
        self.assertEqual(cm.compare_cfg_dict(self.sample_wrong_cfg), False)

if __name__ == "__main__":
    unittest.main()
