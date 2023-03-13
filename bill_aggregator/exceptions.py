class BillAggBaseException(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class BillAggConfigError(BillAggBaseException):

    def __init__(self, message="Config Error"):
        super().__init__(message)


class BillAggException(BillAggBaseException):

    def __init__(self, message="An exception occured"):
        super().__init__(message)
