class LLMError(Exception):
    pass


class LLMHTTPError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMTimeoutError(LLMError):
    pass