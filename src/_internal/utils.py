def check(cond: bool, message: str | None = None) -> None:
    if not cond:
        raise AssertionError(message)
