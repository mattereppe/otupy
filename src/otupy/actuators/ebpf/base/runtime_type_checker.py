from functools import wraps
import inspect
from typing import Callable, Any

def runtime_type_check(func: Callable) -> Callable:
    sig = inspect.signature(func)
    annotations = func.__annotations__

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        for name, value in bound.arguments.items():
            if name in annotations and annotations[name] not in (None, Any):
                if not isinstance(value, annotations[name]):
                    raise TypeError(f"{func.__name__} arg {name} expected {annotations[name]}, got {type(value)}")
        result = func(*args, **kwargs)
        if "return" in annotations and annotations["return"] not in (None, Any):
            if not isinstance(result, annotations["return"]):
                raise TypeError(f"{func.__name__} return expected {annotations['return']}, got {type(result)}")
        return result
    return wrapper