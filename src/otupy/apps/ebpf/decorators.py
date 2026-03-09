from .plugin_registry import ProducerPluginRegistry

def producer_plugin(name: str):
    def wrapper(cls):
        ProducerPluginRegistry.register(name, cls)
        cls.plugin_name = name
        return cls
    return wrapper