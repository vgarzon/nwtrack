"""
Simple dependency injection container.
"""

from __future__ import annotations

from typing import Callable, Any, Self, cast
from enum import StrEnum


class Lifetime(StrEnum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"


type Provider[T] = Callable[[Container], T]


class Container:
    def __init__(self) -> None:
        # have to store *neterogeneous* providers, so use Any instead of T
        self._providers: dict[Any, tuple[Provider[Any], Lifetime]] = {}
        self._singletons: dict[Any, Any] = {}

    def register[T](
        self,
        token: Any,
        provider: Provider[T],
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> Self:
        """
        Register a provider for token that returns T.

        Example:

            container.register(Config, lambda c: Config(...))  # T = Config
        """
        # Provider[T] is safely storable as Provider[Any] at runtime
        self._providers[token] = (cast(Provider[Any], provider), lifetime)
        return self

    def resolve[T](self, token: type[T] | Any) -> T:
        """
        Resolve a token to its instance of type T.

        Example:
            cfg = container.resolve(Config)  # inferred type: Config
        """
        if token in self._singletons:
            return cast(T, self._singletons[token])

        try:
            provider_any, lifetime = self._providers[token]
        except KeyError:
            raise KeyError(f"No provider registered for '{token!r}'.")

        # provider_any is Provider[Any] at runtime, but statically it's Provider[T]
        provider = cast(Provider[T], provider_any)

        # call provider with self (the container) to allow auto-injection
        instance = provider(self)

        if lifetime == Lifetime.SINGLETON:
            self._singletons[token] = instance

        return instance
