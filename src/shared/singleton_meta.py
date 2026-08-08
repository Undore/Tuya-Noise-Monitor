from typing import Self, cast


class SingletonMeta(type):
    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls in cls._instances:
            return cls._instances[cls]

        if Singleton in cls.__bases__:
            raise RuntimeError(
                f"Use .get_instance() to initialize {cls.__qualname__}, "
                "because it is a singleton"
            )

        instance = super().__call__(*args, **kwargs)
        cls._instances[cls] = instance

        return instance

    @classmethod
    def get_instance(cls, class_: type):
        if class_ not in cls._instances:
            cls._instances[class_] = type.__call__(class_)

        return cls._instances[class_]


class Singleton(metaclass=SingletonMeta):
    @classmethod
    def get_instance(cls) -> Self:
        return cast(
            Self,
            SingletonMeta.get_instance(cls),
        )