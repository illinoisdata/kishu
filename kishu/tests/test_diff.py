import pytest

from kishu.diff import DiffAlgorithms, KishuDiff


class TestDiff:
    @pytest.mark.parametrize(
        "origin, destination, expected",
        [
            (
                ["a", "b\nc\nd\ne", "c", "d", "e"],
                ["j", "a", "b\nd\ne", "d", "e", "f"],
                [
                    "Destination_only",
                    "Both",
                    "Origin_only",
                    "Origin_only",
                    "Destination_only",
                    "Both",
                    "Both",
                    "Destination_only",
                ],
            ),
            (
                ["a", "b\nc\nd\ne", "c\nc\nc", "d", "e"],
                ["j", "a", "c\na\nc", "b\nd\ne", "d", "e", "f"],
                [
                    "Destination_only",
                    "Both",
                    "Origin_only",
                    "Origin_only",
                    "Destination_only",
                    "Destination_only",
                    "Both",
                    "Both",
                    "Destination_only",
                ],
            ),
            (
                ["a", "b\nc\nd\ne", "c", "d", "e", "k", "f\nh\n", "p"],
                ["j", "a", "b\nd\ne", "d", "e", "f\nh\ni\n", "p"],
                [
                    "Destination_only",
                    "Both",
                    "Origin_only",
                    "Origin_only",
                    "Destination_only",
                    "Both",
                    "Both",
                    "Origin_only",
                    "Origin_only",
                    "Destination_only",
                    "Both",
                ],
            ),
            (
                ["a", "b", "c\no"],
                ["a", "b", "d", "c\ne\no"],
                ["Both", "Both", "Origin_only", "Destination_only", "Destination_only"],
            ),
        ],
    )
    def test_myre_diff(self, origin, destination, expected):
        result = DiffAlgorithms.myre_diff(origin, destination)
        assert [hunk.option for hunk in result.diff_hunks] == expected

    @pytest.mark.parametrize(
        "origin, destination, expected",
        [
            (
                ["a", "b\nc\nd\ne", "c", "d", "e"],
                ["j", "a", "b\nd\ne", "d", "e", "f"],
                ["Destination_only", "Both", "Both", "Origin_only", "Both", "Both", "Destination_only"],
            ),
            (
                ["a", "b\nc\nd\ne", "c\nc\nc", "d", "e"],
                ["j", "a", "c\na\nc", "b\nd\ne", "d", "e", "f"],
                ["Destination_only", "Both", "Destination_only", "Both", "Origin_only", "Both", "Both", "Destination_only"],
            ),
            (
                ["a", "b\nc\nd\ne", "c", "d", "e", "k", "f\nh\n", "p"],
                ["j", "a", "b\nd\ne", "d", "e", "f\nh\ni\n", "p"],
                ["Destination_only", "Both", "Both", "Origin_only", "Both", "Both", "Origin_only", "Both", "Both"],
            ),
            (["a", "b", "c\no"], ["a", "b", "d", "c\ne\no"], ["Both", "Both", "Destination_only", "Both"]),
        ],
    )
    def test_edr_diff(self, origin, destination, expected):
        result = DiffAlgorithms.edr_diff(origin, destination)
        assert [hunk.option for hunk in result.diff_hunks] == expected

    @pytest.mark.parametrize(
        "origin, destination, expected",
        [
            (
                ["a", "b\nc\nd\ne", "c", "d", "e"],
                ["j", "a", "b\nd\ne", "d", "e", "f"],
                ["Destination_only", "Both", "Both", "Origin_only", "Both", "Both", "Destination_only"],
            ),
            (
                ["a", "b\nc\nd\ne", "c\nc\nc", "d", "e"],
                ["j", "a", "c\na\nc", "b\nd\ne", "d", "e", "f"],
                ["Destination_only", "Both", "Destination_only", "Both", "Origin_only", "Both", "Both", "Destination_only"],
            ),
            (
                ["a", "b\nc\nd\ne", "c", "d", "e", "k", "f\nh\n", "p"],
                ["j", "a", "b\nd\ne", "d", "e", "f\nh\ni\n", "p"],
                ["Destination_only", "Both", "Both", "Origin_only", "Both", "Both", "Origin_only", "Both", "Both"],
            ),
            (
                ["a", "b\nc\nd\ne", "c", "aa\ncc", "d", "e", "k", "b\nc\nd\ne", "f\nh\n", "p"],
                ["j", "a", "b\nd\ne", "gg", "aa\nbb\ncc", "d", "e", "b\nc\nd\ne", "f\nh\ni\n", "p"],
                [
                    "Destination_only",
                    "Both",
                    "Both",
                    "Origin_only",
                    "Destination_only",
                    "Both",
                    "Both",
                    "Both",
                    "Origin_only",
                    "Both",
                    "Both",
                    "Both",
                ],
            ),
            (
                ["a", "b\nc\nd\ne", "c", "aa\ncc", "d", "e", "k", "b\nc\nd\ne", "f\nh\n", "p", "b\nc\nd\ne", "c", "aa\ncc"],
                [
                    "j",
                    "a",
                    "b\nd\ne",
                    "gg",
                    "aa\nbb\ncc",
                    "d",
                    "e",
                    "b\nd\ne",
                    "f\nh\ni\n",
                    "p",
                    "b\nd\ne",
                    "gg",
                    "aa\nbb\ncc",
                ],
                [
                    "Destination_only",
                    "Both",
                    "Both",
                    "Origin_only",
                    "Destination_only",
                    "Both",
                    "Both",
                    "Both",
                    "Origin_only",
                    "Both",
                    "Both",
                    "Both",
                    "Both",
                    "Origin_only",
                    "Destination_only",
                    "Both",
                ],
            ),
        ],
    )
    def test_kishu_get_diff(self, origin, destination, expected):
        result = KishuDiff.diff_cells(origin, destination)
        assert [hunk.option for hunk in result] == expected
