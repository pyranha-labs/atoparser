"""Global fixtures for pytest."""

import asyncio
import inspect
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from types import GeneratorType
from typing import Any

import pytest

# Loaded by dotted path rather than defined here. A non-root conftest may not declare this; the root
# one is the only supported place, and this is it.
pytest_plugins = ()

# The result keys a test case may declare, exactly one of which is mandatory.
RESULT_KEYS = ("returns", "raises", "attributes")


def _execute_test(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Run a function, or coroutine function, safely in pytest and return the result."""
    # A custom executor converts async to sync: a new loop cannot be created from the main thread, and
    # pytest's own event loop will not allow new tasks to be run directly.
    if inspect.iscoroutinefunction(func):
        with ThreadPoolExecutor(1) as pool:
            return pool.submit(asyncio.run, func(*args, **kwargs)).result()
    result = func(*args, **kwargs)
    # A sync function that returned an awaitable has that awaitable run to completion on a fresh loop.
    if inspect.isawaitable(result):
        awaitable = result

        async def _await_result() -> Any:
            """Await what the call already returned."""
            return await awaitable

        result = _execute_test(_await_result)
    return result


def _finalize_test(test: dict, result: Any, compare: Callable[[Any, Any], bool] | None) -> None:
    """Validate the result of running a test against what the test case expected."""
    attributes = test.get("attributes")
    if attributes is not None and not attributes:
        raise ValueError("Test attributes result type must have values")
    if attributes:
        actual = {name: getattr(result, name) for name in attributes}
        expected = attributes
    else:
        actual = result
        expected = test.get("returns")
    equals = compare(actual, expected) if compare else actual == expected
    assert equals, f"\nResult:\n\t{actual}\nExpected:\n\t{expected}"


@pytest.fixture(name="function_tester")
def fixture_function_tester() -> Callable[..., None]:
    """Return a callable that runs one declared test case against a function.

    Returns:
        The test runner, which takes a test case and the callable under test.
    """

    def function_tester(
        test: dict,
        func: Callable,
        *,
        compare: Callable[[Any, Any], bool] | None = None,
        drain: bool = True,
        monkeypatch: pytest.MonkeyPatch | None = None,
    ) -> None:
        """Run one test case against a callable.

        Test case guidelines:
            - To test output, declare `args` and/or `kwargs` plus `returns`.
            - To test failure, declare `args` and/or `kwargs` plus `raises`.
              A (type, match) tuple is used to compare since type alone cannot tell one refusal from another.
            - To test an object, pass the class as `func` and declare `attributes`.
            - To patch first, declare `patches` as (target, name, value) tuples and pass `monkeypatch`.

        Args:
            test: The test case. Optional `args`, `kwargs`, and `patches`.
                Exactly one of `returns`, `raises`, or `attributes` is mandatory.
            func: The callable to pass the arguments to, sync or async.
            compare: How to compare the actual and expected results. Defaults to equality.
            drain: Whether to convert a generator result into a list before comparing.
            monkeypatch: pytest's patching fixture, required when the test case declares `patches`.

        Raises:
            ValueError: When the test case declares other than one result, or declares `patches` with no `monkeypatch`.
        """
        args, kwargs, raises, patches = _initialize_test(test)
        if patches:
            if monkeypatch is None:
                raise ValueError("Test declares patches but no monkeypatch was passed")
            for target, name, value in patches:
                _patch_test(target, name, value, monkeypatch=monkeypatch)
        if raises:
            exception, match = raises
            with pytest.raises(exception, match=match):
                result = _execute_test(func, *args, **kwargs)
                if drain and isinstance(result, GeneratorType):
                    list(result)
        else:
            result = _execute_test(func, *args, **kwargs)
            if drain and isinstance(result, GeneratorType):
                result = list(result)
            _finalize_test(test, result, compare)

    return function_tester


def _initialize_test(
    test: dict,
) -> tuple[list, dict, tuple[type[BaseException], str] | None, list[tuple] | None]:
    """Pull out the arguments for running a test, rejecting a test case that declares no single result."""
    declared = [name for name in RESULT_KEYS if name in test]
    if not declared:
        raise ValueError(f"Test must declare one of: {', '.join(RESULT_KEYS)}")
    if len(declared) > 1:
        raise ValueError(f"Test must declare only one of: {', '.join(RESULT_KEYS)}")
    return test.get("args", []), test.get("kwargs", {}), test.get("raises"), test.get("patches")


def _patch_test(target: Any, name: str, value: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Apply one temporary patch while a test is running."""
    # Read through a class or static method to the function it wraps: reached through its class, a class method comes
    # back already bound, and would read as no function at all.
    attribute = inspect.getattr_static(target, name)
    original = attribute.__func__ if isinstance(attribute, (classmethod, staticmethod)) else getattr(target, name)
    if not inspect.isfunction(original):
        monkeypatch.setattr(target, name, value)
        return
    patched = value
    # Allow a plain callable, such as a lambda, to stand in for an async one.
    if inspect.iscoroutinefunction(original) and not inspect.iscoroutinefunction(value):

        async def await_value(*args: Any, **kwargs: Any) -> Any:
            """Await the replacement so it matches the signature it is standing in for."""
            result = value(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        patched = await_value

    # Allow a plain callable to stand in for a class or static method.
    if isinstance(attribute, staticmethod) and not isinstance(patched, staticmethod):
        patched = staticmethod(patched)
    elif isinstance(attribute, classmethod) and not isinstance(patched, classmethod):
        patched = classmethod(patched)
    monkeypatch.setattr(target, name, patched)


def pytest_configure(config: pytest.Config) -> None:
    """Add the `parametrize_tests` marker to the pytest configuration.

    Args:
        config: The pytest configuration.
    """
    config.addinivalue_line(
        "markers",
        "parametrize_tests: Mark a test function as parametrized with a mapping of entries that supplies the args and IDs.",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Expand the `parametrize_tests` marker, taking pytest ids from the test case names.

    Args:
        metafunc: The test being collected.
    """
    mark = metafunc.definition.get_closest_marker("parametrize_tests")
    if not mark:
        return
    args = list(mark.args)
    if len(args) == 1:
        args = ["test"] + args
    tests = args[1]
    args[1] = list(tests.values()) if isinstance(tests, dict) else list(tests)
    kwargs = dict(mark.kwargs)
    kwargs["ids"] = [str(name) for name in (tests.keys() if isinstance(tests, dict) else tests)]
    metafunc.parametrize(*args, **kwargs)
