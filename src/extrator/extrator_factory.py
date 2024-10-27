import inspect
import importlib
import pkgutil

from extrator.extrator import Extrator

def instanciar(txt):
    package = importlib.import_module('extrator')

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"extrator.{module_name}")
    
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                obj.__module__ == module.__name__
                and issubclass(obj, Extrator) 
                and obj is not Extrator
                and hasattr(obj, 'pode_usar') 
                and callable(getattr(obj, 'pode_usar')) 
                and obj.pode_usar(txt)
            ):
                return obj(txt)

    raise ValueError(f"Não foi encontrado um extrator válido")
