from aiogram import Router

from processes.telegram.register_hooks import register_hooks

ROUTER_REGISTRY = []

def register_router(name: str) -> Router:
    router = Router(name=name)
    ROUTER_REGISTRY.append(router)
    return router

register_hooks()
