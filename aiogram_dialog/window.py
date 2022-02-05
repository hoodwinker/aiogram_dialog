from logging import getLogger
from typing import Dict, Optional, Union, List

from aiogram.dispatcher.filters.state import State
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery, ParseMode, ForceReply

from .dialog import Dialog, DialogWindowProto, DataGetter
from .manager.protocols import DialogManager
from .utils import get_chat, NewMessage, remove_message
from .widgets.action import Actionable
from .widgets.input import BaseInput, MessageHandlerFunc
from .widgets.kbd import Keyboard
from .widgets.text import Text
from .widgets.utils import ensure_widgets

logger = getLogger(__name__)


class Window(DialogWindowProto):

    def __init__(self,
                 *widgets: Union[str, Text, Keyboard, MessageHandlerFunc, BaseInput],
                 state: State,
                 getter: DataGetter = None,
                 parse_mode: Optional[ParseMode] = None,
                 disable_web_page_preview: Optional[bool] = None,
                 preview_add_transitions: Optional[List[Keyboard]] = None,
                 preview_data: Optional[Dict] = None,
                 force_reply_placeholder: Optional[Union[str, bool]] = None,
                 remove_on_close: Optional[bool] = None,
                 input_removing: Optional[bool] = None,
                 ):
        self.text, self.keyboard, self.on_message = ensure_widgets(widgets)
        self.getter = getter
        self.state = state
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.preview_add_transitions = preview_add_transitions
        self.preview_data = preview_data
        self.force_reply_placeholder = force_reply_placeholder
        self._remove_on_close = remove_on_close
        self._input_removing = input_removing
        self._message_id = None

    async def render_text(self, data: Dict, manager: DialogManager) -> str:
        return await self.text.render_text(data, manager)

    async def render_kbd(self, data: Dict, manager: DialogManager) -> InlineKeyboardMarkup:
        keyboard = await self.keyboard.render_keyboard(data, manager)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def load_data(self, dialog: "Dialog", manager: DialogManager) -> Dict:
        if not self.getter:
            return {}
        return await self.getter(**manager.data)

    async def process_message(self, message: Message, dialog: Dialog, manager: DialogManager):
        if self.on_message:
            await self.on_message.process_message(message, dialog, manager)
        if self._input_removing:
            await remove_message(manager.event.bot, message)

    async def process_callback(self, c: CallbackQuery, dialog: Dialog, manager: DialogManager):
        if self.keyboard:
            await self.keyboard.process_callback(c, dialog, manager)

    async def render(self, dialog: Dialog, manager: DialogManager, preview: bool = False) -> NewMessage:
        logger.debug("Show window: %s", self)
        if preview:
            current_data = self.preview_data
        else:
            current_data = await self.load_data(dialog, manager)

        reply_markup = await self.render_kbd(current_data, manager)

        if self.force_reply_placeholder is not None and self.force_reply_placeholder is not True:
            if reply_markup.inline_keyboard:
                raise RuntimeError("Cannot use force reply and keyboard simultaneously")
            else:
                if self.force_reply_placeholder is True:
                    reply_markup = ForceReply()
                else:
                    reply_markup = ForceReply(input_field_placeholder=self.force_reply_placeholder)

        force_new = any((
            all((isinstance(manager.event, Message), not self._input_removing)),
            self.force_reply_placeholder
        ))

        return NewMessage(
            chat=get_chat(manager.event),
            text=await self.render_text(current_data, manager),
            reply_markup=reply_markup,
            parse_mode=self.parse_mode,
            force_new=force_new,
            disable_web_page_preview=self.disable_web_page_preview,
        )

    def get_state(self) -> State:
        return self.state

    @property
    def remove_on_close(self):
        return self._remove_on_close

    @property
    def message_id(self) -> Optional[int]:
        return self._message_id

    @message_id.setter
    def message_id(self, value):
        self._message_id = value

    def find(self, widget_id) -> Optional[Actionable]:
        if self.keyboard:
            res = self.keyboard.find(widget_id)
            if res:
                return res
        if self.on_message:
            return self.on_message.find(widget_id)
        return None

    def __repr__(self):
        return f"<{self.__class__.__qualname__}({self.state})>"
