from dataclasses import dataclass

import pytest
from typing import Generator, List

from kishu.diff import DiffAlgorithms, KishuDiff


@dataclass
class ODCellSequence:
    origin: List[str]
    destination: List[str]


@pytest.fixture()
def od_cell_sequences() -> Generator[List[ODCellSequence], None, None]:
    yield [
        # one add-remove group(1 add + 2 remove) between two initial exact-matched groups
        ODCellSequence(
            origin=["a", "b\nc\nd\ne", "c", "d", "e"],
            destination=["j", "a", "b\nd\ne", "d", "e", "f"],
        ),
        # one add-remove group(2 add + 2 remove but with wrong order, the algorithm should prefer to match the more
        ODCellSequence(
            origin=["a", "b\nc\nd\ne", "c\nc\nc", "d", "e"],
            destination=["j", "a", "c\na\nc", "b\nd\ne", "d", "e", "f"],
        ),
        # two add-remove groups (each group 1 add + 2 removes) between three initial exact-matched groups
        ODCellSequence(
            origin=["a", "b\nc\nd\ne", "c", "d", "e", "k", "f\nh\n", "p"],
            destination=["j", "a", "b\nd\ne", "d", "e", "f\nh\ni\n", "p"],
        ),
        # two add-remove groups (each group has multiple add + multiple removes and has multiple matchings) between
        # three
        ODCellSequence(
            origin=["a", "b\nc\nd\ne", "c", "aa\ncc", "d", "e", "k", "b\nc\nd\ne", "f\nh\n", "p"],
            destination=["j", "a", "b\nd\ne", "gg", "aa\nbb\ncc", "d", "e", "b\nc\nd\ne", "f\nh\ni\n", "p"],
        ),
        # corner case: having add-remove pairs at the end while the test is complex
        ODCellSequence(
            origin=["a", "b\nc\nd\ne", "c", "aa\ncc", "d", "e", "k", "b\nc\nd\ne", "f\nh\n", "p", "b\nc\nd\ne", "c",
                    "aa\ncc"],
            destination=["j", "a", "b\nd\ne", "gg", "aa\nbb\ncc", "d", "e", "b\nc\nd\ne", "f\nh\ni\n", "p", "b\nd\ne",
                         "gg", "aa\nbb\ncc"],
        ),
        # corner case: having add-remove pairs at the end
        ODCellSequence(
            origin=["a", "b", "c\no"],
            destination=["a", "b", "d", "c\ne\no"]),

    ]


class TestDiff:
    def test_myre_diff(self, od_cell_sequences):
        result = DiffAlgorithms.myre_diff(od_cell_sequences[0].origin, od_cell_sequences[0].destination)
        assert [hunk.option for hunk in result.diff_hunks] == ["Destination_only", "Both", "Origin_only", "Origin_only",
                                                               "Destination_only", "Both", "Both", "Destination_only"]

        result = DiffAlgorithms.myre_diff(od_cell_sequences[1].origin, od_cell_sequences[1].destination)
        assert [hunk.option for hunk in result.diff_hunks] == ["Destination_only", "Both", "Origin_only", "Origin_only",
                                                               "Destination_only", "Destination_only", "Both", "Both",
                                                               "Destination_only"]

        result = DiffAlgorithms.myre_diff(od_cell_sequences[2].origin, od_cell_sequences[2].destination)
        assert [hunk.option for hunk in result.diff_hunks] == ["Destination_only", "Both", "Origin_only", "Origin_only",
                                                               "Destination_only", "Both", "Both", "Origin_only",
                                                               "Origin_only", "Destination_only", "Both"]

        result = DiffAlgorithms.myre_diff(od_cell_sequences[5].origin, od_cell_sequences[5].destination)
        assert [hunk.option for hunk in result.diff_hunks] == ["Both", "Both", "Origin_only", "Destination_only",
                                                               "Destination_only"]

    def test_edr_diff(self, od_cell_sequences):
        result = DiffAlgorithms.edr_diff(od_cell_sequences[0].origin, od_cell_sequences[0].destination)
        assert [hunk.option for hunk in result.diff_hunks] == ["Destination_only", "Both", "Both", "Origin_only",
                                                               "Both", "Both", "Destination_only"]

        result = DiffAlgorithms.edr_diff(od_cell_sequences[1].origin, od_cell_sequences[1].destination)
        assert [hunk.option for hunk in result.diff_hunks] == ["Destination_only", "Both", "Destination_only",
                                                               "Both", "Origin_only", "Both", "Both",
                                                               "Destination_only"]

        result = DiffAlgorithms.edr_diff(od_cell_sequences[2].origin, od_cell_sequences[2].destination)
        assert [hunk.option for hunk in result.diff_hunks] == ["Destination_only", "Both", "Both", "Origin_only",
                                                               "Both", "Both", "Origin_only", "Both", "Both"]

        result = DiffAlgorithms.edr_diff(od_cell_sequences[5].origin, od_cell_sequences[5].destination)
        assert [hunk.option for hunk in result.diff_hunks] == ["Both", "Both", "Destination_only",
                                                               "Both"]

    def test_kishu_get_diff(self, od_cell_sequences):
        result = KishuDiff.kishu_get_diff(od_cell_sequences[0].origin, od_cell_sequences[0].destination)
        assert [hunk.option for hunk in result.cell_diff_hunks] == ["Destination_only", "Both", "Both",
                                                                    "Origin_only", "Both", "Both",
                                                                    "Destination_only"]

        result = KishuDiff.kishu_get_diff(od_cell_sequences[1].origin, od_cell_sequences[1].destination)
        assert [hunk.option for hunk in result.cell_diff_hunks] == ["Destination_only", "Both", "Destination_only",
                                                                    "Both", "Origin_only", "Both", "Both",
                                                                    "Destination_only"]

        result = KishuDiff.kishu_get_diff(od_cell_sequences[2].origin, od_cell_sequences[2].destination)
        assert [hunk.option for hunk in result.cell_diff_hunks] == ["Destination_only", "Both", "Both",
                                                                    "Origin_only", "Both", "Both", "Origin_only",
                                                                    "Both", "Both"]

        result = KishuDiff.kishu_get_diff(od_cell_sequences[3].origin, od_cell_sequences[3].destination)
        assert [hunk.option for hunk in result.cell_diff_hunks] == ["Destination_only", "Both", "Both",
                                                                    "Origin_only", "Destination_only", "Both",
                                                                    "Both", "Both", "Origin_only", "Both", "Both",
                                                                    "Both"]

        result = KishuDiff.kishu_get_diff(od_cell_sequences[4].origin, od_cell_sequences[4].destination)
        assert [hunk.option for hunk in result.cell_diff_hunks] == ["Destination_only", "Both", "Both",
                                                                    "Origin_only", "Destination_only", "Both",
                                                                    "Both", "Both", "Origin_only", "Both", "Both",
                                                                    "Both", "Both", "Origin_only",
                                                                    "Destination_only", "Both"]
