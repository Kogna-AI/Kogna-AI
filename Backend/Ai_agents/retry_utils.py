"""
Retry utilities with exponential backoff for AI agent API calls.
"""
import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Optional, Tuple, Type
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delays
            retry_exceptions: Tuple of exception types to retry on
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions


def calculate_delay(
    attempt: int,
    initial_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool
) -> float:
    """
    Calculate the delay for the next retry attempt.
    
    Args:
        attempt: Current attempt number (0-indexed)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter
    
    Returns:
        Delay in seconds
    """
    # Calculate exponential delay
    delay = min(initial_delay * (exponential_base ** attempt), max_delay)
    
    # Add jitter if enabled (±25% randomization)
    if jitter:
        jitter_range = delay * 0.25
        delay = delay + random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay)  # Ensure non-negative
    
    return delay


def should_retry(exception: Exception, retry_exceptions: Tuple[Type[Exception], ...]) -> bool:
    """
    Determine if an exception should trigger a retry.
    
    Args:
        exception: The exception that occurred
        retry_exceptions: Tuple of exception types to retry on
    
    Returns:
        True if should retry, False otherwise
    """
    if isinstance(exception, retry_exceptions):
        # Check for specific error messages that indicate retryable errors
        error_msg = str(exception).lower()
        retryable_keywords = [
            'timeout',
            'rate limit',
            'too many requests',
            '429',
            '503',
            '504',
            'service unavailable',
            'connection error',
            'connection reset',
            'broken pipe'
        ]
        
        return any(keyword in error_msg for keyword in retryable_keywords)
    
    return False


def retry_with_backoff(
    config: Optional[RetryConfig] = None
) -> Callable:
    """
    Decorator that implements exponential backoff retry logic.
    
    Args:
        config: RetryConfig object with retry parameters
    
    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    # Attempt the function call
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not should_retry(e, config.retry_exceptions):
                        logger.warning(f"Non-retryable exception in {func.__name__}: {e}")
                        raise
                    
                    # Check if we've exhausted retries
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) exceeded for {func.__name__}. "
                            f"Last error: {e}"
                        )
                        raise
                    
                    # Calculate delay and wait
                    delay = calculate_delay(
                        attempt,
                        config.initial_delay,
                        config.max_delay,
                        config.exponential_base,
                        config.jitter
                    )
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_retries} failed for {func.__name__}. "
                        f"Error: {str(e)[:200]}. Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


# Predefined configurations for different scenarios
DEFAULT_CONFIG = RetryConfig(
    max_retries=5,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

AGGRESSIVE_CONFIG = RetryConfig(
    max_retries=3,
    initial_delay=0.5,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True
)

PATIENT_CONFIG = RetryConfig(
    max_retries=7,
    initial_delay=2.0,
    max_delay=120.0,
    exponential_base=2.0,
    jitter=True
)


def retry_llm_call(func: Callable[..., T]) -> Callable[..., T]:
    """
    Convenience decorator for LLM API calls with sensible defaults.
    """
    return retry_with_backoff(DEFAULT_CONFIG)(func)