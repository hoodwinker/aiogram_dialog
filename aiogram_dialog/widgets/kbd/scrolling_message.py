import bisect
import re
from typing import Dict, List

from aiogram.types import CallbackQuery, InlineKeyboardButton

from aiogram_dialog import DialogManager, Dialog
from aiogram_dialog.widgets.kbd import Keyboard
from aiogram_dialog.widgets.text import Text
from aiogram_dialog.widgets.when import WhenCondition


class ScrollingMessage(Keyboard, Text):
    def __init__(self,
                 text_format: str,
                 id: str,
                 limit: int = None,
                 split_by=None,
                 when: WhenCondition = None):
        super().__init__(id=id, when=when)
        if not limit:
            limit = 4096
        self.limit = limit
        self.split_by = split_by or '\n'

        self.splitters = ['\n', ' ', '']
        if self.split_by in self.splitters:
            self.splitters.remove(self.split_by)
        self.splitters = [self.split_by, *self.splitters]

        self.text = text_format

    async def _render_text(self, data: Dict, manager: DialogManager) -> str:
        text = self.text.format_map(data)
        pages = self.get_pages(text, manager)
        last_page = len(pages) - 1

        current_page = min(last_page, self.get_page(manager))

        start, end = pages[current_page]
        text = text[start: end]
        return text

    async def _render_keyboard(self, data: Dict, manager: DialogManager) -> List[List[InlineKeyboardButton]]:
        text = self.text.format_map(data)
        pages = self.get_pages(text, manager)
        last_page = len(pages) - 1
        if last_page <= 1:
            return []

        current_page = min(last_page, self.get_page(manager))
        next_page = min(last_page, current_page + 1)
        prev_page = max(0, current_page - 1)

        pager = [[
            InlineKeyboardButton(text="1", callback_data=f"{self.widget_id}:0"),
            InlineKeyboardButton(text="<", callback_data=f"{self.widget_id}:{prev_page}"),
            InlineKeyboardButton(text=str(current_page + 1), callback_data=f"{self.widget_id}:{current_page}"),
            InlineKeyboardButton(text=">", callback_data=f"{self.widget_id}:{next_page}"),
            InlineKeyboardButton(text=str(last_page + 1), callback_data=f"{self.widget_id}:{last_page}"),
        ]]
        return pager

    async def process_callback(self, c: CallbackQuery, dialog: Dialog, manager: DialogManager) -> bool:
        prefix = f"{self.widget_id}:"
        if not c.data.startswith(prefix):
            return await super().process_callback(c, dialog, manager)
        new_page = int(c.data[len(prefix):])
        await self.set_page(new_page, manager)
        return True

    def get_pages(self, text, manager: DialogManager):
        pages = manager.current_context().widget_data.get('pages', None)
        return pages or self.calc_pages(text)

    def calc_pages(self, text):
        return list(self.calc_pages_helper(text))

    def calc_pages_helper(self, text):
        last_pos = 0

        for split_by in self.splitters:
            splitters = [m.start() for m in re.finditer(split_by, text[last_pos:])] + [len(text)]

            while True:
                splitter = bisect.bisect_right(splitters, self.limit)
                if not splitter:
                    break
                else:
                    max_len = splitters[splitter - 1]

                yield last_pos, max_len + last_pos
                last_pos = max_len + last_pos

                splitters = (splitters[i] - max_len for i, _ in enumerate(splitters))
                splitters = list(filter(lambda x: x <= 0, splitters))

            if last_pos == len(text):
                break

            if len(text) - last_pos < self.limit:
                yield last_pos, len(text)
                break

    def get_page(self, manager: DialogManager) -> int:
        return manager.current_context().widget_data.get('page', 0)

    async def set_page(self, page: int, manager: DialogManager):
        manager.current_context().widget_data['page'] = page
