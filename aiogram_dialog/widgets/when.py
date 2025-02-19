from typing import Union, Callable, Dict, Sequence

from magic_filter import MagicFilter

from .managed import ManagedWidget
from ..manager.protocols import DialogManager

Predicate = Callable[[Dict, "Whenable", DialogManager], bool]
WhenCondition = Union[str, MagicFilter, Predicate, None]

__all__ = ['WhenCondition', 'Whenable', 'when_not', 'when_all']


def new_when_field(fieldname: str) -> Predicate:
    def when_field(data: Dict, widget: "Whenable",
                   manager: DialogManager) -> bool:
        return bool(data.get(fieldname))

    return when_field


def new_when_magic(f: MagicFilter) -> Predicate:
    def when_magic(data: Dict, widget: "Whenable", manager: DialogManager) -> bool:
        return f.resolve(data)

    return when_magic


def true(data: Dict, widget: "Whenable", manager: DialogManager):
    return True


def when_not(fieldname: str) -> Predicate:
    def _when_not(data: Dict, widget: "Whenable", manager: DialogManager) -> bool:
        return not bool(data.get(fieldname))

    return _when_not


def when_all(fields: Sequence[WhenCondition]) -> Predicate:
    def check_field(when_field: WhenCondition, data, widget, manager):
        if isinstance(when_field, str):
            return bool(data.get(when_field))
        else:
            return when_field(data, widget, manager)

    def _when_all(data: Dict, widget: "Whenable", manager: DialogManager) -> bool:
        return all(map(lambda field: check_field(field, data, widget, manager), fields))

    return _when_all


class Whenable(ManagedWidget):

    def __init__(self, when: WhenCondition = None):
        self.condition: Predicate
        if when is None:
            self.condition = true
        elif isinstance(when, str):
            self.condition = new_when_field(when)
        elif isinstance(when, MagicFilter):
            self.condition = new_when_magic(when)
        else:
            self.condition = when

    def is_(self, data, manager):
        return self.condition(data, self, manager)
