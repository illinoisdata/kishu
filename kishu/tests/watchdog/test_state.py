import pytest

import dill as pickle
import sys
import types

from kishu.exceptions import TypeNotSupportedError
from kishu.watchdog.state import ContinuousPickler, Scope, State


"""
TestFrameParsing
"""


def dummy_function_frame(i=9):
    a = 1
    b = "2"  # noqa
    c = [3]  # noqa
    d = {4}  # noqa
    e = {5: 5}  # noqa

    def f():
        return 6

    g = a + f()  # noqa
    h = type(8)  # noqa
    return sys._getframe()


def dummy_deep_function_frame(depth=3):
    if depth > 1:
        return dummy_deep_function_frame(depth=depth-1)
    x = 1  # noqa
    y = "2"  # noqa
    return sys._getframe()


def unserializable_generator():
    for idx in range(10):
        yield idx


class TestFrameParsing:
    """Tests parsing from frame object to Frame."""

    def test_function_frame(self):
        state = State.parse_from([dummy_function_frame()])
        assert len(state.get_frames()) == 1
        frame = state.get_frames()[0]

        # Test get
        assert frame.get("a") == 1
        assert frame.get("b") == "2"
        assert frame.get("c") == [3]
        assert frame.get("d") == {4}
        assert frame.get("e") == {5: 5}
        assert isinstance(frame.get("f"), types.FunctionType) and frame.get("f")() == 6
        assert frame.get("g") == 7
        assert frame.get("h") == int
        assert frame.get("i") == 9

        # Test get_cells
        cells = frame.get_cells()
        assert len(cells) == 9
        assert cells["a"] == 1
        assert cells["b"] == "2"
        assert cells["c"] == [3]
        assert cells["d"] == {4}
        assert cells["e"] == {5: 5}
        assert isinstance(cells["f"], types.FunctionType) and cells["f"]() == 6
        assert cells["g"] == 7
        assert cells["h"] == int
        assert cells["i"] == 9

        # Test get_execution
        execution = frame.get_execution()
        assert execution.lasti > 0  # Could be flaky to specify this.
        assert execution.lineno > 0  # Could be flaky to specify this.

        # Test serializable
        serialized_frame = pickle.dumps(frame)
        assert len(serialized_frame) > 0

    def test_deep_function_frame_frame(self):
        state = State.parse_from([dummy_deep_function_frame()])
        assert len(state.get_frames()) == 1
        frame = state.get_frames()[0]

        # Test get
        assert frame.get("x") == 1
        assert frame.get("y") == "2"
        assert frame.get("depth") == 1

        # Test get_cells
        cells = frame.get_cells()
        assert len(cells) == 3
        assert cells["x"] == 1
        assert cells["y"] == "2"
        assert cells["depth"] == 1

        # Test get_execution
        execution = frame.get_execution()
        assert execution.lasti > 0  # Could be flaky to specify this.
        assert execution.lineno > 0  # Could be flaky to specify this.

        # Test serializable
        serialized_frame = pickle.dumps(frame)
        assert len(serialized_frame) > 0

    def test_many_frames(self):
        state = State.parse_from([dummy_function_frame(), dummy_function_frame()])
        assert len(state.get_frames()) == 2

    @pytest.mark.parametrize(
        "not_supported_obj",
        [
            unserializable_generator(),  # GeneratorType, TODO: enable this
            sys._getframe(),  # FrameType
        ]
    )
    def test_fail_type_not_supported(self, not_supported_obj):
        with pytest.raises(TypeNotSupportedError):
            Scope.parse_from({"not_supported_obj": not_supported_obj})


"""
TestContinuousPickling
"""


class TestContinuousPickling:

    def test_smaller_size_when_shared(self):
        a = [idx for idx in range(1000)]
        b = [a]

        pickler = ContinuousPickler()
        shared_size = len(pickler.dumps(a)) + len(pickler.dumps(b))

        pickler = ContinuousPickler()
        a_size = len(pickler.dumps(a))
        pickler = ContinuousPickler()
        b_size = len(pickler.dumps(b))
        separated_size = a_size + b_size

        assert shared_size < separated_size

    def test_not_smaller_size_when_not_shared(self):
        a = [idx for idx in range(1000)]
        b = [idx for idx in range(1000)]

        pickler = ContinuousPickler()
        shared_size = len(pickler.dumps(a)) + len(pickler.dumps(b))

        pickler = ContinuousPickler()
        a_size = len(pickler.dumps(a))
        pickler = ContinuousPickler()
        b_size = len(pickler.dumps(b))
        separated_size = a_size + b_size

        assert shared_size >= separated_size
