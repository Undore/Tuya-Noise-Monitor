from typing import Self

import async_lru
from pydantic import BaseModel



class BaseModelV2(BaseModel):
    @classmethod
    def make_dict(cls, entity) -> dict:
        return {
            key: value
            for key, value in entity.__dict__.items()
            if not key.startswith('_')
        }

    @classmethod
    def serialize(cls, entity, *args, **kwargs):
        for arg in args:
            if isinstance(arg, BaseModel):
                kwargs = {**kwargs, **arg.model_dump()}
            else:
                kwargs = {**kwargs, **cls.make_dict(arg)}

        serialized_data = cls.make_dict(entity)

        return cls.serialize_dict(serialized_data, **kwargs)

    @classmethod
    def s_dict(cls, input_dict: dict, **kwargs):
        return cls.serialize_dict(input_dict, **kwargs)

    @classmethod
    def serialize_dict(cls, input_dict: dict, **kwargs):
        dct = input_dict.copy()
        for key, value in kwargs.items():
            dct[key] = value

        # noinspection PyArgumentList
        pydantic_instance = cls(**dct)

        return pydantic_instance

    @classmethod
    def s(cls, entity, *args, **kwargs) -> Self:
        return cls.serialize(entity, *args, **kwargs)

    @classmethod
    def serialize_list(cls, entities: list) -> list[Self]:
        return [cls.s(e) for e in entities]

    @classmethod
    def s_list(cls, entities: list) -> list[Self]:
        return cls.serialize_list(entities)

    class Config:
        # noinspection PyProtectedMember
        ignored_types = (async_lru._LRUCacheWrapper, )

