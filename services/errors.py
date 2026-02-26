class AppError(Exception):
    pass


class ValidationError(AppError):
    pass


class NotFoundError(AppError):
    pass


class DuplicateError(AppError):
    pass


class DatabaseError(AppError):
    pass
