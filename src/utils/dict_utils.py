import typing


def remove_nulls(dikt: dict[str, typing.Any]):
    keys = list(dikt.keys())
    for k in keys:
        value = dikt[k]
        if value is None:
            del dikt[k]
        if isinstance(value, dict):
            remove_nulls(value)
