class BillAggBaseException(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class BillAggError(BillAggBaseException):

    def __init__(self, message="An error occured"):
        super().__init__(message)


class BillAggException(BillAggBaseException):

    def __init__(self, message="An exception occured"):
        super().__init__(message)
