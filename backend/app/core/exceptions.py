class PlayerNotFoundException(Exception):
    pass


class MatchNotFoundException(Exception):
    pass


class MatchAlreadyExistsException(Exception):
    pass


class PlayerAlreadyInQueueException(Exception):
    pass


class PlayerNotInQueueException(Exception):
    pass
