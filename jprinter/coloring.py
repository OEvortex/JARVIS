"""
>>> from jprinter.coloring import JARVIS
>>>
>>> print(JARVIS.styles)
{<Token.Text: 0>: '#ffffff', <Token.Whitespace: 1>: '#222222', <Token.Error: 2>: '#ff0000', ...}
>>> from jprinter.coloring import create_custom_style
>>> colors = {<Token.Text>: "#ff00ff"}
>>> custom_style = create_custom_style("MyCustomStyle", colors)
>>> print(custom_style.styles)
{<Token.Text: 0>: '#ff00ff'}

This module defines color styles for the output of the jprint and jp functions. 
It includes a default color scheme, JARVIS, and the ability to create custom 
styles using create_custom_style function.
"""
from pygments.style import Style
from pygments.token import (
    Text, Name, Error, Other, String, Number, Keyword, Generic, Literal,
    Comment, Operator, Whitespace, Punctuation)
class JARVIS(Style):
    background_color = "#000000"
    styles = {
        Text:                   "#ffffff",
        Whitespace:             "#222222",
        Error:                  "#ff0000",
        Other:                  "#ffffff",
        Name:                   "#00ffff",
        Name.Attribute:         "#ffffff",
        Name.Builtin:           "#00ff00",
        Name.Builtin.Pseudo:    "#00ff00",
        Name.Class:             "#00ff00",
        Name.Constant:          "#ffff00",
        Name.Decorator:         "#ff8800",
        Name.Entity:            "#ff8800",
        Name.Exception:         "#ff8800",
        Name.Function:          "#00ff00",
        Name.Property:          "#00ff00",
        Name.Label:             "#ffffff",
        Name.Namespace:         "#ffff00",
        Name.Other:             "#ffffff",
        Name.Tag:               "#00ff88",
        Name.Variable:          "#ff8800",
        Name.Variable.Class:    "#00ff00",
        Name.Variable.Global:   "#00ff00",
        Name.Variable.Instance: "#00ff00",
        String:                 "#88ff00",
        String.Backtick:        "#88ff00",
        String.Char:            "#88ff00",
        String.Doc:             "#88ff00",
        String.Double:          "#88ff00",
        String.Escape:          "#ff8800",
        String.Heredoc:         "#88ff00",
        String.Interpol:        "#ff8800",
        String.Other:           "#88ff00",
        String.Regex:           "#88ff00",
        String.Single:          "#88ff00",
        String.Symbol:          "#88ff00",
        Number:                 "#0088ff",
        Number.Float:           "#0088ff",
        Number.Hex:             "#0088ff",
        Number.Integer:         "#0088ff",
        Number.Integer.Long:    "#0088ff",
        Number.Oct:             "#0088ff",
        Keyword:                "#ff00ff",
        Keyword.Constant:       "#ff00ff",
        Keyword.Declaration:    "#ff00ff",
        Keyword.Namespace:      "#ff8800",
        Keyword.Pseudo:         "#ff8800",
        Keyword.Reserved:       "#ff00ff",
        Keyword.Type:           "#ff00ff",
        Generic:                "#ffffff",
        Generic.Deleted:        "#ffffff",
        Generic.Emph:           "#ffffff",
        Generic.Error:          "#ffffff",
        Generic.Heading:        "#ffffff",
        Generic.Inserted:       "#ffffff",
        Generic.Output:         "#ffffff",
        Generic.Prompt:         "#ffffff",
        Generic.Strong:         "#ffffff",
        Generic.Subheading:     "#ffffff",
        Generic.Traceback:      "#ffffff",
        Literal:                "#ffffff",
        Literal.Date:           "#ffffff",
        Comment:                "#888888",
        Comment.Multiline:      "#888888",
        Comment.Preproc:        "#888888",
        Comment.Single:         "#888888",
        Comment.Special:        "#888888",
        Operator:               "#ffffff",
        Operator.Word:          "#ff00ff",
        Punctuation:            "#ffffff",
    }
def create_custom_style(name, colors):
    return type(name, (Style,), {'styles': colors})