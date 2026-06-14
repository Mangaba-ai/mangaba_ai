"""
Lógica de repetição com back-off exponencial para chamadas LLM.
"""

from __future__ import annotations

import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Set, Type, TypeVar

from mangaba.core.exceptions import RetryableError, RateLimitError, LLMError
from mangaba.core.events import EventBus, Event, EventType

log = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Any])

_DEFAULT_RETRYABLE: Set[Type[Exception]] = {
    RetryableError,
    RateLimitError,
    ConnectionError,
    TimeoutError,
}


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Optional[Set[Type[Exception]]] = None,
) -> Callable[[F], F]:
    """Decorador que repete uma função em erros transitórios.

    Usa back-off exponencial com jitter opcional para evitar problemas
    de thundering herd. Emite eventos LLM_RETRY para o EventBus em cada tentativa de repetição.

    Args:
        max_retries: Número máximo de tentativas de repetição (0 = sem repetições, padrão: 3).
        backoff_factor: Fator de back-off multiplicativo entre repetições (padrão: 2.0).
        max_delay: Limite superior no atraso em segundos (padrão: 60.0).
        jitter: Adiciona jitter aleatório ao atraso para evitar thundering herd (padrão: True).
        retryable_exceptions: Conjunto de tipos de exceção que acionam uma repetição.
            Padrão para RetryableError, RateLimitError, ConnectionError, TimeoutError.

    Returns:
        Uma função decoradora que envolve a função alvo com lógica de repetição.

    Raises:
        LLMError: Se todas as tentativas de repetição forem esgotadas.
    """
    exceptions = retryable_exceptions or _DEFAULT_RETRYABLE

    def decorator(fn: F) -> F:
        """Decorador que aplica lógica de repetição à função.

        Args:
            fn: A função para envolver com lógica de repetição.

        Returns:
            A função envolvida com lógica de repetição aplicada.
        """

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Função wrapper que implementa a lógica de repetição.

            Args:
                *args: Argumentos posicionais para passar para a função envolvida.
                **kwargs: Argumentos de palavra-chave para passar para a função envolvida.

            Returns:
                O valor de retorno da função envolvida em sucesso.

            Raises:
                LLMError: Se todas as tentativas de repetição forem esgotadas.
            """
            last_exc: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except tuple(exceptions) as exc:
                    last_exc = exc
                    if attempt >= max_retries:
                        break

                    # Compute delay
                    delay = min(backoff_factor**attempt, max_delay)
                    if isinstance(exc, RateLimitError) and exc.retry_after:
                        delay = max(delay, exc.retry_after)
                    if jitter:
                        delay *= 0.5 + random.random()

                    EventBus.emit(
                        Event(
                            event_type=EventType.LLM_RETRY,
                            data={
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "delay": round(delay, 2),
                                "error": str(exc),
                            },
                        )
                    )
                    log.warning(
                        "Retry %d/%d after %.1fs – %s",
                        attempt + 1,
                        max_retries,
                        delay,
                        exc,
                    )
                    time.sleep(delay)

            raise LLMError(
                f"Failed after {max_retries} retries: {last_exc}",
                cause=last_exc,
            )

        return wrapper  # type: ignore[return-value]

    return decorator
