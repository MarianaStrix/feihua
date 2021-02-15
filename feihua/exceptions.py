class ClientError(Exception):
    def __init__(self, status, data, *args):
        super().__init__(status, data, *args)
        self.status = status
        self.message = data["message"]

    def __str__(self):
        return f"ClientError({self.status}, {self.message!r})"

    def __repr__(self):
        return self.__str__()
