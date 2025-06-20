import os

import yaml

# 确保数据目录存在
os.makedirs("data/database", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/output", exist_ok=True)


class Config:
    def __init__(self, config_dict):
        self._data = {}
        for k, v in config_dict.items():
            if isinstance(v, dict):
                v = Config(v)
            self._data[k] = v

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value


def load_config(yaml_path="config.yaml"):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config(data)
