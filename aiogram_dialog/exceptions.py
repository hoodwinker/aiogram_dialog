class DialogsError(RuntimeError):
    pass


# intents and stack
class InvalidStackIdError(DialogsError):
    pass


class InvalidIntentIdError(DialogsError):
    pass


class UnknownIntent(DialogsError):
    pass


class OutdatedIntent(DialogsError):
    def __init__(self, intent_id, stack_id, text):
        super().__init__(text)
        self.intent_id = intent_id
        self.stack_id = stack_id


class UnknownState(DialogsError):
    pass


class DialogStackOverflow(DialogsError):
    pass


# manager
class IncorrectBackgroundError(DialogsError):
    pass


# navigation
class UnregisteredDialogError(DialogsError):
    pass


class UnregisteredWindowError(DialogsError):
    pass


# widgets
class InvalidWidgetIdError(DialogsError):
    pass


class InvalidWidget(DialogsError):
    pass


class InvalidWidgetType(InvalidWidget):
    pass
