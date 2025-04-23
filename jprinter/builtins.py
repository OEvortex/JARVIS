from .jprint import jprint
try:
    builtins = __import__('__builtin__')
except ImportError:
    builtins = __import__('builtins')
def install(ic='jprint'):
    setattr(builtins, ic, jprint)
def uninstall(ic='jprint'):
    delattr(builtins, ic)
