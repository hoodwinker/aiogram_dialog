from logging import getLogger
from typing import Dict, Optional, List, Union

from aiogram.dispatcher.filters.state import State
from aiogram.types import (
    InlineKeyboardMarkup, Message, CallbackQuery, ParseMode, ForceReply as ForceReplyMarkup
)

from .dialog import Dialog, DialogWindowProto
from .manager.protocols import DialogManager, ShowMode
from .utils import get_chat, NewMessage, MediaAttachment, remove_message
from .widgets.action import Actionable
from .widgets.data import PreviewAwareGetter
from .widgets.kbd import Keyboard
from .widgets.utils import (
    ensure_widgets, ensure_data_getter, GetterVariant, WidgetSrc,
)

logger = getLogger(__name__)


class Window(DialogWindowProto):
    def __init__(self,
                 *widgets: WidgetSrc,
                 state: State,
                 getter: GetterVariant = None,
                 parse_mode: Optional[ParseMode] = None,
                 disable_web_page_preview: Optional[bool] = None,
                 preview_add_transitions: Optional[List[Keyboard]] = None,
                 preview_data: GetterVariant = None,
                 remove_on_close: Optional[bool] = None,
                 input_removing: Optional[bool] = None,
                 ):
        (
            self.text, self.keyboard, self.on_message, self.media,
        ) = ensure_widgets(widgets)
        self.getter = PreviewAwareGetter(
            ensure_data_getter(getter),
            ensure_data_getter(preview_data),
        )
        self.state = state
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.preview_add_transitions = preview_add_transitions
        self.preview_data = preview_data
        self._remove_on_close = remove_on_close
        self._input_removing = input_removing
        self._message_id = None

    async def render_text(self, data: Dict, manager: DialogManager) -> str:
        return await self.text.render_text(data, manager)

    async def render_media(
            self, data: Dict,
            manager: DialogManager
    ) -> Optional[MediaAttachment]:
        if self.media:
            return await self.media.render_media(data, manager)

    async def render_kbd(self, data: Dict,
                         manager: DialogManager) -> Union[InlineKeyboardMarkup, ForceReplyMarkup]:
        keyboard = await self.keyboard.render_keyboard(data, manager)

        if isinstance(keyboard, ForceReplyMarkup):
            return keyboard
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def load_data(self, dialog: "Dialog",
                        manager: DialogManager) -> Dict:
        return await self.getter(**manager.data)

    async def process_message(self, message: Message, dialog: Dialog,
                              manager: DialogManager):
        if self.on_message:
            await self.on_message.process_message(message, dialog, manager)
        if self._input_removing:
            event_message_is_last = True
            if manager.current_stack().last_message_id is not None:
                if message.message_id > manager.current_stack().last_message_id:
                    event_message_is_last = False
            else:
                event_message_is_last = False

            if event_message_is_last:
                await remove_message(manager.event.bot, message)

    async def process_callback(self, c: CallbackQuery, dialog: Dialog,
                               manager: DialogManager):
        if self.keyboard:
            await self.keyboard.process_callback(c, dialog, manager)

    async def render(self, dialog: Dialog, manager: DialogManager) -> NewMessage:
        logger.debug("Show window: %s", self)
        current_data = await self.load_data(dialog, manager)
        reply_markup = await self.render_kbd(current_data, manager)

        message_is_last = True
        if isinstance(manager.event, Message):
            if manager.current_stack().last_message_id is not None:
                if manager.current_stack().last_message_id < manager.event.message_id:
                    message_is_last = False
            else:
                message_is_last = False

        force_new = any((
            all((isinstance(manager.event, Message), not self._input_removing, not message_is_last)),
            isinstance(reply_markup, ForceReplyMarkup),
            manager.show_mode is ShowMode.SEND
        ))

        return NewMessage(
            chat=get_chat(manager.event),
            text=await self.render_text(current_data, manager),
            reply_markup=reply_markup,
            parse_mode=self.parse_mode,
            show_mode=ShowMode.SEND if force_new else ShowMode.EDIT,
            disable_web_page_preview=self.disable_web_page_preview,
            media=await self.render_media(current_data, manager),
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
