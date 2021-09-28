class DialogsError(RuntimeError):
    pass


# intents and stack
class InvalidStackIdError(DialogsError):
    pass


class InvalidIntentIdError(DialogsError):
    pass


class OutdatedIntentError(DialogsError):
    pass


class UnknownIntent(DialogsError):
    pass


class UnknownState(DialogsError):
    pass


class DialogStackOverflow(DialogsError):
    pass


# manager
class IncorrectBackgroundError(DialogsError):
    pass


# widgets
class InvalidWidgetIdError(DialogsError):
    pass


class InvalidWidget(DialogsError):
    pass


class InvalidWidgetType(InvalidWidget):
    pass
