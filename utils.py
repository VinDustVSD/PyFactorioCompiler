from typing import Iterable

from terminal import Terminal


class TerminalUtil:
    @staticmethod
    def get_pretty(term: Terminal, prename="", tab="   ", is_last=True):
        if isinstance(term, Iterable) and not isinstance(term, str):
            text = ('└──' if is_last else '├──') + prename + str(type(term))
            items = [item for item in term]

            for i in range(len(items)):
                item = items[i]
                is_next_last = (i == len(items) - 1)
                pretty_child = TerminalUtil.get_pretty(
                    item,
                    prename=str(i) + ':',
                    tab=tab + ('│  ' if not (is_last and is_next_last) and is_last else '   '),
                    is_last=is_next_last
                )
                text += f"\n{tab}{pretty_child}"

            return text

        if not isinstance(term, Terminal):
            return ('└──' if is_last else '├──') + prename + str(term)

        values = {
            name: getattr(term, name)
            for name in dir(term)
            if not (
                callable(getattr(term, name)) or
                (name in dir(term.__class__) and isinstance(getattr(term.__class__, name), property)) or
                name.startswith("_") or
                name.startswith("n_") or
                name in ["name"]
            )
        }

        text = f"{'└──' if is_last else '├──'}{prename}{term.name}"
        if len(values) == 0:
            raise AssertionError(f"Values of terminal '{term.name}' not found")

        for key in values:
            is_next_last = (key == list(values.keys())[-1])
            pretty_child = TerminalUtil.get_pretty(
                values[key],
                prename=key + ':',
                tab=tab + ('│  ' if not(is_last and is_next_last) and is_last else '   '),
                is_last=is_next_last
            )
            text += f"\n{tab}{pretty_child}"

        return text
