import os

from terminal import *
from terminal.base import *


def collect_terminals():
    terminals = {}
    for filename in os.listdir(os.path.dirname(__file__)):
        if not filename.startswith("_") and filename.endswith(".py"):
            module = __import__("terminal." + filename[:-3])
            module = getattr(module, filename[:-3])
            for key in dir(module):
                item = getattr(module, key)
                if type(item) == type and issubclass(item, Terminal):
                    terminals[key] = item

    return terminals


def get_terminal_name(term: Type['Terminal']):
    name = ""
    for char in term.__name__:
        if char.isupper() and len(name) > 0 and name[-1].islower():
            char = "_" + char
        name += char

    return name.lower()


def _init_terminals(terminals) -> dict[str, Type['Terminal']]:
    named_terminals = {}

    for key in terminals:
        if key.lower() in ["terminal", "example"]:
            continue

        term: Type[Terminal] = terminals[key]
        term.name = get_terminal_name(term)
        named_terminals[term.name] = term

    return {key: named_terminals[key] for key in reversed(named_terminals)}


raw_terminals = collect_terminals()
all_terminals = _init_terminals(raw_terminals)

__all__ = {
    "all_terminals": all_terminals,
    **raw_terminals
}
