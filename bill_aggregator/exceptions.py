class BillAggregatorException(Exception):

    def __init__(self, message="An exception occured"):
        super().__init__(message)
