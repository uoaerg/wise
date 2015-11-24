import json

class ConfigManager():
    def __init__(self, a_cfg_file='foxcfg.json'):
        self.cfg_file = a_cfg_file

    def get_cfg_dict(self):
        try:
            with open(self.cfg_file) as f:
                cfg = json.load(f)
        except:
            cfg = dict()
        return cfg

    def store_cfg_dict(self, a_dict):
        with open(self.cfg_file, 'w') as f:
            json.dump(a_dict, f)

    def get_key_value(self, a_key):
        cfg = self.get_cfg_dict()
        if a_key in cfg:
            return cfg[a_key]
        else:
            print('Key ' + a_key + ' does not exist in config.')

    def get_key_values(self, a_key_list):
        cfg = self.get_cfg_dict()
        values = list()
        for index in range(0,len(a_key_list)):
            values.append(cfg[a_key_list[index]])
        return values

    def set_key_value(self, a_key, a_value):
        cfg = self.get_cfg_dict()
        cfg[a_key] = a_value
        self.store_cfg_dict(cfg)

    def set_key_values(self, a_key_list, a_value_list):
        if len(a_key_list) == len(a_value_list):
            cfg = self.get_cfg_dict()
            for index in range(0,len(a_key_list)):
                cfg[a_key_list[index]] = a_value_list[index]
            self.store_cfg_dict(cfg)
        else:
            print('Key and value lists not same length.')

    def compare_cfg_dict(self, a_cfg_dict):
        current_cfg = self.get_cfg_dict()
        for key in current_cfg:
            if key not in a_cfg_dict:
                return False
        for key in a_cfg_dict:
            if key not in current_cfg:
                return False
        return True
