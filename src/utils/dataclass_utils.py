import inspect


class BaseDataClass:

    @classmethod
    def from_dict(cls, dikt: dict) -> 'BaseDataClass':
        # noinspection PyArgumentList
        return cls(**cls.remove_extra_fields(dikt))

    @classmethod
    def remove_extra_fields(cls, dikt: dict) -> dict:
        # fetch the constructor's signature
        cls_fields = {field for field in inspect.signature(cls).parameters}

        # split the kwargs into native ones and new ones
        native_args = {}
        for name, val in dikt.items():
            if name in cls_fields:
                native_args[name] = val

        return native_args

    @classmethod
    def get_extra_fields(cls, dikt: dict) -> dict:
        # fetch the constructor's signature
        cls_fields = {field for field in inspect.signature(cls).parameters}

        # split the kwargs into native ones and new ones
        extra_args = {}
        for name, val in dikt.items():
            if name not in cls_fields:
                extra_args[name] = val

        return extra_args
