"""
>>> from jprinter.core import JPrintDebugger
>>>
>>> debugger = JPrintDebugger(prefix="DEBUG >>> ")
>>> debugger("Hello", "world!")
DEBUG >>> [__main__.py:3] in () >>> Hello, world!
>>> debugger.format("Formatted output")
'DEBUG >>> [__main__.py:5] in () >>> Formatted output'
>>>
This module contains the core logic for the jprint and jp functions.
It includes the JPrintDebugger class, which is responsible for formatting
and outputting debug information, source code analysis for variable
names, colorizing output, and configurable options.
"""
#!/usr/bin/env python
from __future__ import print_function
import ast
import inspect
import pprint
import sys
import warnings
from datetime import datetime
import functools
from contextlib import contextmanager
from os.path import basename, realpath
from textwrap import dedent
import colorama
import executing
from pygments import highlight
from pygments.formatters import Terminal256Formatter, HtmlFormatter
from pygments.lexers import PythonLexer as PyLexer, Python3Lexer as Py3Lexer
from pygments.token import Token
from typing import Any, List, Type, Optional
from .coloring import JARVIS, create_custom_style
import json
_absent = object()
def bindStaticVariable(name, value):
    def decorator(fn):
        setattr(fn, name, value)
        return fn
    return decorator
@bindStaticVariable('formatter', Terminal256Formatter(style=JARVIS))
@bindStaticVariable(
    'lexer', Py3Lexer(ensurenl=False))
def colorize(s, color_style=None):
    if color_style is None:
        formatter = Terminal256Formatter(style=JARVIS)
    elif isinstance(color_style, dict):
        CustomStyle = create_custom_style('CustomStyle', color_style)
        formatter = Terminal256Formatter(style=CustomStyle)
    else:
        formatter = Terminal256Formatter(style=color_style)
    return highlight(s, colorize.lexer, formatter)
@contextmanager
def supportTerminalColorsInWindows():
    colorama.init()
    yield
    colorama.deinit()
def stderrPrint(*args, sep=' ', end='\n', flush=False):
    print(*args, file=sys.stderr, sep=sep, end=end, flush=flush)
def isLiteral(s):
    try:
        ast.literal_eval(s)
    except Exception:
        return False
    return True
def colorizedStderrPrint(s, color_style=None, sep=' ', end='\n', flush=False):
    colored = colorize(s, color_style)
    with supportTerminalColorsInWindows():
        stderrPrint(colored, sep=sep, end=end, flush=flush)
DEFAULT_PREFIX = 'JARVIS -> '
DEFAULT_LINE_WRAP_WIDTH = 70
DEFAULT_CONTEXT_DELIMITER = '- '
DEFAULT_OUTPUT_FUNCTION = colorizedStderrPrint
DEFAULT_ARG_TO_STRING_FUNCTION = pprint.pformat
NO_SOURCE_AVAILABLE_WARNING_MESSAGE = (
    'Failed to access the underlying source code for analysis. Was jprint() '
    'invoked in a REPL (e.g. from the command line), a frozen application '
    '(e.g. packaged with PyInstaller), or did the underlying source code '
    'change during execution?')
def callOrValue(obj):
    return obj() if callable(obj) else obj
class Source(executing.Source):
    def get_text_with_indentation(self, node):
        result = self.asttokens().get_text(node)
        if '\n' in result:
            result = ' ' * node.first_token.start[1] + result
            result = dedent(result)
        result = result.strip()
        return result
def prefixLines(prefix, s, startAtLine=0):
    lines = s.splitlines()
    for i in range(startAtLine, len(lines)):
        lines[i] = prefix + lines[i]
    return lines
def prefixFirstLineIndentRemaining(prefix, s):
    indent = ' ' * len(prefix)
    lines = prefixLines(indent, s, startAtLine=1)
    lines[0] = prefix + lines[0]
    return lines
def formatPair(prefix, arg, value):
    if arg is _absent:
        argLines = []
        valuePrefix = prefix
    else:
        argLines = prefixFirstLineIndentRemaining(prefix, arg)
        valuePrefix = argLines[-1] + ': '
    looksLikeAString = (value[0] + value[-1]) in ["''", '""']
    if looksLikeAString:
        valueLines = prefixLines(' ', value, startAtLine=1)
        value = '\n'.join(valueLines)
    if isinstance(value, str) and len(value) > JPrintDebugger.lineWrapWidth:
        valueLines = []
        for i in range(0, len(value), JPrintDebugger.lineWrapWidth):
            valueLines.extend(prefixFirstLineIndentRemaining(valuePrefix, value[i:i+JPrintDebugger.lineWrapWidth]))
            valuePrefix = ' ' * len(valuePrefix)
        lines = argLines[:-1] + valueLines
    else:
        valueLines = prefixFirstLineIndentRemaining(valuePrefix, value)
        lines = argLines[:-1] + valueLines
    return '\n'.join(lines)
def singledispatch(func):
    func = functools.singledispatch(func)
    closure = dict(zip(func.register.__code__.co_freevars, 
                       func.register.__closure__))
    registry = closure['registry'].cell_contents
    dispatch_cache = closure['dispatch_cache'].cell_contents
    def unregister(cls):
        del registry[cls]
        dispatch_cache.clear()
    func.unregister = unregister
    return func
@singledispatch
def argumentToString(obj, **kwargs):
   
    if isinstance(obj, str):
        return obj
    
    try:
        return json.dumps(obj, indent=2)
    except TypeError:
        return obj
class JPrintDebugger:
    _pairDelimiter = ', '
    lineWrapWidth = DEFAULT_LINE_WRAP_WIDTH
    contextDelimiter = DEFAULT_CONTEXT_DELIMITER
    global_enabled = True
    def __init__(self, prefix: str = DEFAULT_PREFIX,
                 outputFunction: Any = DEFAULT_OUTPUT_FUNCTION,
                 argToStringFunction: Any = argumentToString, includeContext: bool = True,
                 contextAbsPath: bool = False, log_file: Optional[str] = None, color_style: Any | None = None,
                 disable_colors: bool = False, contextDelimiter: str = DEFAULT_CONTEXT_DELIMITER,
                 log_timestamp: bool = False, style: str = 'default', filter_types: Optional[List[Type]] = None, flush: bool = False,
                 pprint_options: Optional[dict] = None, rich_styles: Optional[dict] = None):
        self.enabled = True
        self.prefix = prefix
        self.includeContext = includeContext
        self.outputFunction = outputFunction if outputFunction is not None else DEFAULT_OUTPUT_FUNCTION
        self.argToStringFunction = argToStringFunction
        self.contextAbsPath = contextAbsPath
        self.log_file = log_file
        self.color_style = color_style
        self.disable_colors = disable_colors
        self.contextDelimiter = contextDelimiter if contextDelimiter is not None else ''
        self.log_timestamp = log_timestamp
        self.style = style
        self.filter_types = filter_types
        self.flush = flush
        self.pprint_options = pprint_options if pprint_options is not None else {}
        self.rich_styles = rich_styles if rich_styles is not None else {}
    def __call__(self, *args):
        if self.enabled and JPrintDebugger.global_enabled:
            callFrame = inspect.currentframe().f_back
            formatted_output = self._format(callFrame, *args)
            if self.disable_colors:
                with supportTerminalColorsInWindows():
                    stderrPrint(formatted_output, flush=self.flush)
            else:
                self.outputFunction(formatted_output, self.color_style)
            if self.log_file:
                self._log_output(formatted_output)
        if not args:
            passthrough = None
        elif len(args) == 1:
            passthrough = args[0]
        else:
            passthrough = args
        return passthrough
    def format(self, *args):
        callFrame = inspect.currentframe().f_back
        out = self._format(callFrame, *args)
        return out
    def _format(self, callFrame, *args):
        prefix = callOrValue(self.prefix)
        context = self._formatContext(callFrame) if self.includeContext else ''
        if not args:
            time = self._formatTime()
            out = prefix + context + time
        else:
            out = self._formatArgs(
                callFrame, prefix, context, args)
        if not context:
            self.contextDelimiter = ''
        return out
    def _formatArgs(self, callFrame, prefix, context, args):
        callNode = Source.executing(callFrame).node
        if callNode is not None:
            source = Source.for_frame(callFrame)
            sanitizedArgStrs = [
                source.get_text_with_indentation(arg)
                for arg in callNode.args]
        else:
            warnings.warn(
                NO_SOURCE_AVAILABLE_WARNING_MESSAGE,
                category=RuntimeWarning, stacklevel=4)
            sanitizedArgStrs = [_absent] * len(args)
        pairs = list(zip(sanitizedArgStrs, args))
        if self.filter_types:
            pairs = [(arg, val) for arg, val in pairs if any(isinstance(val, t) for t in self.filter_types)]
        out = self._constructArgumentOutput(prefix, context, pairs)
        return out
    def _constructArgumentOutput(self, prefix, context, pairs):
        def argPrefix(arg):
            return '%s : ' % arg
        pairs = [(arg, self.argToStringFunction(val, **self.pprint_options)) for arg, val in pairs]
        
        if len(pairs) == 0:
            return prefix + context
        
        if len(pairs) == 1:
             arg, val = pairs[0]
             if arg is _absent or isLiteral(arg):
                return prefix + context + f" >>> {val}"
             else:
                return prefix + context + f" >>> {argPrefix(arg)}{val}"
        
        
        pairStrs = [
            val if (isLiteral(arg) or arg is _absent)
            else (argPrefix(arg) + val)
            for arg, val in pairs]
            
        allArgsOnOneLine =  ", ".join(pairStrs)
        
        contextDelimiter = self.contextDelimiter if context else ''
        
        return prefix + context + contextDelimiter + allArgsOnOneLine
            
    def _formatContext(self, callFrame):
        filename, lineNumber, parentFunction = self._getContext(callFrame)
        if parentFunction == "<module>":
            parentFunction = "()"
        else:
            parentFunction = '%s()' % parentFunction
        context = '[%s:%s] in %s' % (filename, lineNumber, parentFunction)
        return context
    def _formatTime(self):
        now = datetime.now()
        formatted = now.strftime('%H:%M:%S.%f')[:-3]
        return ' at %s' % formatted
    def _getContext(self, callFrame):
        
        frames = inspect.stack()
        
        # Start from the frame where _getContext is called (which is 2 frames back)
        for frame_info in frames[2:]:
            if frame_info.function not in  ['_formatContext', '_format', 'jp', 'jprint', 'log']: # Skip jprint internals
                
                lineNumber = frame_info.lineno
                parentFunction = frame_info.function
                filepath = (realpath if self.contextAbsPath else basename)(frame_info.filename)
                
                
                return filepath, lineNumber, parentFunction
        
        # If no other frame is found, return module information
        frameInfo = inspect.getframeinfo(callFrame)
        lineNumber = frameInfo.lineno
        parentFunction = frameInfo.function
        filepath = (realpath if self.contextAbsPath else basename)(frameInfo.filename)
        return filepath, lineNumber, parentFunction
    def enable(self):
        self.enabled = True
    def disable(self):
        self.enabled = False
    def _log_output(self, output):
        with open(self.log_file, 'a') as f:
            if self.log_timestamp:
                now = datetime.now()
                formatted = now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                f.write(f'[{formatted}] {output}\n')
            else:
                f.write(output + '\n')