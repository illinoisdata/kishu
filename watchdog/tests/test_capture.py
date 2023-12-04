import pytest

import sys

from watchdog.capture import StandardPythonCapture


"""
TestStandardPythonCapture
"""


def dummy_variable_depth(depth, truncate_at_depth, capture_depth, truncated_id):
    if depth == truncate_at_depth:
        truncated_id = id(sys._getframe())

    if depth > 1:
        return dummy_variable_depth(depth-1, truncate_at_depth, capture_depth, truncated_id)
    else:
        return StandardPythonCapture.capture_state(
            depth=capture_depth,
            truncate_at_frame_id=truncated_id,
        )


def dummy_capture_twice(
    depth,
    capture_twice_at_depth,
    truncated_id,
):
    if depth == capture_twice_at_depth:
        StandardPythonCapture.capture_state(truncate_at_frame_id=truncated_id)

    if depth > 1:
        return dummy_capture_twice(depth-1, capture_twice_at_depth, truncated_id)
    else:
        return StandardPythonCapture.capture_state(truncate_at_frame_id=truncated_id)


class TestStandardPythonCapture:

    @pytest.mark.parametrize(
        "depth,truncate_at_depth,capture_depth",
        [
            (1, 2, 0),
            (1, 1, 0),
            (1, 2, 1),
            (1, 2, 2),
            (5, 1, 1),
            (5, 2, 2),
            (5, 1, 3),
        ],
    )
    def test_correct_capture_amount(self, depth, truncate_at_depth, capture_depth):
        truncated_base_id = id(sys._getframe())  # Stop here before backtracking into pytest
        state, same_frames = dummy_variable_depth(
            depth,
            truncate_at_depth,
            capture_depth,
            truncated_base_id,
        )
        # starting_depth = min(depth, truncate_at_depth - 1)
        assert len(state.get_frames()) == len(same_frames)
        # assert len(state.get_frames()) == max(starting_depth - capture_depth, 0)
        # assert not any(same_frames)

    @pytest.mark.parametrize(
        "depth,capture_twice_at_depth",
        [
            (1, 2),
            (1, 1),
            (3, 1),
            (3, 2),
            (3, 3),
            (6, 1),
            (6, 2),
            (6, 3),
            (6, 4),
            (6, 5),
            (6, 6),
        ],
    )
    def test_same_frames(self, depth, capture_twice_at_depth):
        truncated_base_id = id(sys._getframe())  # Stop here before backtracking into pytest
        state, same_frames = dummy_capture_twice(
            depth,
            capture_twice_at_depth,
            truncated_base_id,
        )
        assert len(state.get_frames()) == len(same_frames)
        assert len(state.get_frames()) == depth
        # assert sum(same_frames) == depth - (capture_twice_at_depth - 1)
