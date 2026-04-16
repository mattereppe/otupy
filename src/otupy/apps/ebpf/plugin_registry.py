from typing import Dict, Type

class ProducerPluginRegistry:
    _plugins: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, plugin):
        if name in cls._plugins:
            raise ValueError(f"Producer plugin '{name}' already registered")
        cls._plugins[name] = plugin

    @classmethod
    def get(cls, name: str):
        if name not in cls._plugins:
            raise ValueError(f"Producer plugin '{name}' not found")
        return cls._plugins[name]

    @classmethod
    def all(cls):
        return cls._plugins