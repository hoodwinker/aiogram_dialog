from typing import Union, Callable, Dict

from aiogram_dialog.manager.manager import DialogManager

Predicate = Callable[[Dict, "Whenable", DialogManager], bool]
WhenCondition = Union[str, Predicate, None]


__all__ = ['WhenCondition', 'when_not']


def new_when_field(fieldname: str) -> Predicate:
    def when_field(data: Dict, widget: "Whenable", manager: DialogManager) -> bool:
        return bool(data.get(fieldname))

    return when_field


def true(data: Dict, widget: "Whenable", manager: DialogManager):
    return True


def when_not(fieldname: str) -> Predicate:
    def _when_not(data: Dict, widget: "Whenable", manager: DialogManager) -> bool:
        return not bool(data.get(fieldname))

    return _when_not


class Whenable:

    def __init__(self, when: WhenCondition = None):
        self.condition: Predicate
        if when is None:
            self.condition = true
        elif isinstance(when, str):
            self.condition = new_when_field(when)
        else:
            self.condition = when

    def is_(self, data, manager):
        return self.condition(data, self, manager)
