class ServiceError(Exception):
    """Base class for service-layer errors."""


class LoginAlreadyExistsError(ServiceError):
    pass


class InvalidCredentialsError(ServiceError):
    pass


class ProjectNotFoundError(ServiceError):
    pass


class OnlyProjectOwnerAllowedError(ServiceError):
    pass


class UserNotFoundError(ServiceError):
    pass


class ProjectAccessAlreadyExistsError(ServiceError):
    pass


class DocumentNotFoundError(ServiceError):
    pass


class UnsupportedFileTypeError(ServiceError):
    pass


class ProjectStorageLimitExceededError(ServiceError):
    pass
