"""
>>> from jprinter import jprint
>>> from jprinter import jp
>>> from jprinter import install, uninstall
>>> 
>>> jprint("Hello, world!")
JARVIS -> [__main__.py:1] in () >>> Hello, world!
>>>
>>> def my_function():
...    jp(1, 2, 3)
>>> my_function()
JARVIS -> [__main__.py:4] in my_function() >>> 1, 2, 3
>>> install()
>>> ic("This is now the builtins.ic()")
JARVIS -> [__main__.py:7] in () >>> This is now the builtins.ic()
>>> uninstall()

This module provides enhanced print and logging functionalities for Python,
allowing developers to debug their code with style and precision. It
includes the jprint and jp functions for debugging, log for logging, and 
install/uninstall functions for integration into the builtins module.
It also handles colorizing output and provides different styles and customizable 
options. 
"""
from .jprint import jprint, log
from .jp import jp, log
from .core import JPrintDebugger
from .builtins import install, uninstall