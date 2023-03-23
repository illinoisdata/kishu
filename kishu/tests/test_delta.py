import pytest

import dill as pickle
import sys
import types

from kishu.state import State
from kishu.delta import StateDelta


"""
TestDelta
"""

def dummy_parameterized(a, make_b):
    if make_b:
        b = "added"
    c = [a]
    return sys._getframe()


class TestDelta:
    """Tests parsing from frame object to Frame."""

    @pytest.mark.parametrize(
        "from_a,from_make_b,to_a,to_make_b,same_frame,added_names,deleted_names",
        [
            # Same frames
            ("1", True, "1", True, True, [], []),
            ("1", True, "999", True, True, ["a"], []),  # No "c" since "a" is shared.
            ("1", False, "1", True, True, ["make_b", "b"], []),
            ("1", True, "1", False, True, ["make_b"], ["b"]),

            # Different frames
            ("1", True, "1", True, False, ["a", "make_b", "b", "c"], []),
            ("1", True, "999", True, False, ["a", "make_b", "b", "c"], []),
            ("1", False, "1", True, False, ["a", "make_b", "b", "c"], []),
            ("1", True, "1", False, False, ["a", "make_b", "c"], ["b"]),
        ],
    )
    def test_single_frame(
        self,
        from_a,
        from_make_b,
        to_a,
        to_make_b,
        same_frame,
        added_names,
        deleted_names,
    ):
        from_state = State.parse_from([dummy_parameterized(a=from_a, make_b=from_make_b)])
        to_state = State.parse_from([dummy_parameterized(a=to_a, make_b=to_make_b)])
        same_frames = [same_frame]
        assert len(from_state.get_frames()) == 1
        assert len(to_state.get_frames()) == 1

        delta = StateDelta.delta(from_state, to_state, same_frames)
        scope_deltas = delta.get_scope_deltas()
        assert len(scope_deltas) == 1

        scope_delta = scope_deltas[0]
        assert set(scope_delta.get_added().keys()) == set(added_names)
        assert scope_delta.get_deleted() == set(deleted_names)
        assert scope_delta.get_execution() is to_state.get_frames()[0].get_execution()
