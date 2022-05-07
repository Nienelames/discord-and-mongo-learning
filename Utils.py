import AO3

class StoryTypeError(Exception):
    def __init__(self, message):
        super().__init__(message)
        pass

class InvalidLinkError(Exception):
    def __init__(self, message):
        super().__init__(message)
        pass

class DuplicateSiteError(Exception):
    def __init__(self, message):
        super().__init__(message)
        pass

class DuplicateLinkError(Exception):
    def __init__(self, message):
        super().__init__(message)
        pass

class UnknownExceptionError(Exception):
    def __init__(self, message):
        super().__init__(message)
        pass

class MailerExecutionError(Exception):
    def __init__(self, message):
        super().__init__(message)
        pass

class MailNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)
        pass