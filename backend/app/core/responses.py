from fastapi.responses import ORJSONResponse


class SuccessResponse(ORJSONResponse):
    """
    成功响应
    """

    def __init__(self, data=None, msg="ok", code=200, status=200, message=None, **kwargs):
        if message is not None:
            msg = message
        self.data = {
            "code": code,
            "message": msg,
            "data": data
        }
        self.data.update(kwargs)
        super().__init__(content=self.data, status_code=status)


class ErrorResponse(ORJSONResponse):
    """
    失败响应
    """

    def __init__(self, msg="error", code=400, status=400, message=None, **kwargs):
        if message is not None:
            msg = message
        self.data = {
            "code": code,
            "message": msg,
            "data": None
        }
        self.data.update(kwargs)
        super().__init__(content=self.data, status_code=status)
