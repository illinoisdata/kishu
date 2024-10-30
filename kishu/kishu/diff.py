from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class CodeDiffHunk:
    option: str  # origin_only, destination_only, both
    content: str  # if option is both, but contents of origin and destination is similar but not same, then it will
    # show the content of the origin
    sub_diff_hunks: Optional[
        List[CodeDiffHunk]
    ]  # if two similar cells are matched, then sub_diff_hunks will be the line-level Diff-hunk list
    # inside the matched cell


@dataclass
class VariableVersionCompare:
    variable_name: str
    option: str  # origin_only, destination_only, both_same_version, both_different_version

    def __hash__(self):
        return hash((self.variable_name, self.option))


@dataclass
class CodeDiffAlgorithmResult:
    origin_same_idx: List[int]  # origin_same_idx[3] = 5 means origin[3] matches destination[5]
    destination_same_idx: List[int]
    diff_hunks: List[CodeDiffHunk]
    similarity: float  # the similarity score between the two series


class DiffAlgorithms:

    @staticmethod
    def myre_diff(origin: List[str], destination: List[str]) -> CodeDiffAlgorithmResult:
        """
        An implementation of the Myers diff algorithm.
        See http://www.xmailserver.org/diff2.pdf

        @return : list1[3] = 5, means that series1[0] = series2[5],
                     list2[3] = 5, means that series2[3] = series1[5]
        """

        @dataclass
        class Frontier:
            x: int
            history: List[CodeDiffHunk]
            same_idxs: List[Tuple[int, int]]
            matched_num: int

        def one(idx):
            """
            The algorithm Myers presents is 1-indexed; since Python isn't, we
            need a conversion.
            """
            return idx - 1

        a_max = len(origin)
        b_max = len(destination)
        # This marks the farthest-right point along each diagonal in the edit
        # graph, along with the history that got it there
        frontier = {1: Frontier(0, [], [], 0)}
        final_result = CodeDiffAlgorithmResult([], [], [], 0)
        end_flag = False
        for d in range(0, a_max + b_max + 1):
            for k in range(-d, d + 1, 2):
                # This determines whether our next search point will be going down
                # in the edit graph, or to the right.
                #
                # The intuition for this is that we should go down if we're on the
                # left edge (k == -d) to make sure that the left edge is fully
                # explored.
                #
                # If we aren't on the top (k != d), then only go down if going down
                # would take us to territory that hasn't sufficiently been explored
                # yet.
                go_down = k == -d or (k != d and frontier[k - 1].x < frontier[k + 1].x)

                # Figure out the starting point of this iteration. The diagonal
                # offsets come from the geometry of the edit grid - if you're going
                # down, your diagonal is lower, and if you're going right, your
                # diagonal is higher.
                if go_down:
                    old_x, history, same_idxs, matched_num = (
                        frontier[k + 1].x,
                        frontier[k + 1].history,
                        frontier[k + 1].same_idxs,
                        frontier[k + 1].matched_num,
                    )
                    x = old_x
                else:
                    old_x, history, same_idxs, matched_num = (
                        frontier[k - 1].x,
                        frontier[k - 1].history,
                        frontier[k - 1].same_idxs,
                        frontier[k - 1].matched_num,
                    )
                    x = old_x + 1

                # We want to avoid modifying the old history, since some other step
                # may decide to use it.
                history = history[:]
                same_idxs = same_idxs[:]
                y = x - k

                # We start at the invalid point (0, 0) - we should only start building
                # up history when we move off of it.
                if 1 <= y <= b_max and go_down:
                    history.append(CodeDiffHunk("Destination_only", destination[one(y)], sub_diff_hunks=None))
                elif 1 <= x <= a_max:
                    history.append(CodeDiffHunk("Origin_only", origin[one(x)], sub_diff_hunks=None))

                # Chew up as many diagonal moves as we can - these correspond to common lines,
                # and they're considered "free" by the algorithm because we want to maximize
                # the number of these in the output.
                while x < a_max and y < b_max and origin[one(x + 1)] == destination[one(y + 1)]:
                    x += 1
                    y += 1
                    history.append(CodeDiffHunk("Both", origin[one(x)], sub_diff_hunks=None))
                    same_idxs.append((one(x), one(y)))
                    matched_num += 1

                if x >= a_max and y >= b_max:
                    # If we're here, then we've traversed through the bottom-left corner,
                    # and are done.
                    series1_common = [-1] * a_max
                    series2_common = [-1] * b_max
                    for item in same_idxs:
                        series1_common[item[0]] = item[1]
                        series2_common[item[1]] = item[0]
                    similarity = matched_num / max(a_max, b_max)
                    final_result = CodeDiffAlgorithmResult(series1_common, series2_common, history, similarity)
                    end_flag = True
                    break

                else:
                    frontier[k] = Frontier(x, history, same_idxs, matched_num)
            if end_flag:
                break
        return final_result

    @staticmethod
    def edr_diff(origin: List[str], destination: List[str], threshold=0.5) -> CodeDiffAlgorithmResult:
        """
        Used to find the similar cells between two series of cells
        An implementation of the EDR diff algorithm. It considers both order and numeric distance between elements.

        @ param series1: the first series of cells
        @ param series2: the second series of cells
        @ param threshold: If two str have similarity less than threshold, they'll never be regarded as similar
        @return : list1[3] = 5, means that series1[0] = series2[5],
                     list2[3] = 5, means that series2[3] = series1[5]
        """
        m = len(origin)
        n = len(destination)
        edr_matrix = [[float("inf")] * (n + 1) for _ in range(m + 1)]

        # base case
        edr_matrix[0][0] = 0
        behaviors_matrix = [[1] * (n + 1) for _ in range(m + 1)]  # by default. insert

        for i in range(1, m + 1):
            edr_matrix[i][0] = i
            behaviors_matrix[i][0] = 2
        for j in range(1, n + 1):
            edr_matrix[0][j] = j
            behaviors_matrix[0][j] = 1

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                myre = DiffAlgorithms.myre_diff(origin[i - 1].split("\n"), destination[j - 1].split("\n"))
                if myre.similarity < threshold:
                    cost = float("inf")  # never regard as similar
                else:
                    cost = 1 - myre.similarity  # the more similar, the less cost of edit
                edr_matrix[i][j] = min(
                    (cost + edr_matrix[i - 1][j - 1]),  # match
                    (1 + edr_matrix[i][j - 1]),  # insertion
                    (1 + edr_matrix[i - 1][j]),
                )  # deletion
                # if match
                if edr_matrix[i][j] == cost + edr_matrix[i - 1][j - 1]:
                    behaviors_matrix[i][j] = 0
                # if insertion
                elif edr_matrix[i][j] == 1 + edr_matrix[i][j - 1]:
                    behaviors_matrix[i][j] = 1
                # if deletion
                else:
                    behaviors_matrix[i][j] = 2

        similarity = edr_matrix[m][n]
        # find all the match pairs
        i = m
        j = n
        origin_same_idx: List[int] = [-1] * m
        destination_same_idx: List[int] = [-1] * n
        while i > 0 and j > 0:
            if (behaviors_matrix[i][j]) == 0:
                origin_same_idx[i - 1] = j - 1
                destination_same_idx[j - 1] = i - 1
                i -= 1
                j -= 1
            elif (behaviors_matrix[i][j]) == 1:
                j -= 1
            else:
                i -= 1

        # construct the diff hunk
        diff_hunks = []
        j = 0
        for i in range(m):
            if origin_same_idx[i] == -1:
                diff_hunks.append(CodeDiffHunk("Origin_only", origin[i], sub_diff_hunks=None))
            else:
                to = origin_same_idx[i]
                for k in range(j, to):
                    diff_hunks.append(CodeDiffHunk("Destination_only", destination[k], sub_diff_hunks=None))
                line_level_myre = DiffAlgorithms.myre_diff(origin[i].split("\n"), destination[to].split("\n"))
                if abs(line_level_myre.similarity - 1) < 1e-9:
                    line_diff_hunks = None
                else:
                    line_diff_hunks = line_level_myre.diff_hunks
                diff_hunks.append(CodeDiffHunk("Both", origin[i], sub_diff_hunks=line_diff_hunks))
                # if line level diff only contains both, then we should not add this diff hunk, meaning they are the
                # same
                j = to + 1
        for k in range(j, n):
            diff_hunks.append(CodeDiffHunk("Destination_only", destination[k], sub_diff_hunks=None))
        return CodeDiffAlgorithmResult(origin_same_idx, destination_same_idx, diff_hunks, similarity)


class KishuDiff:
    @staticmethod
    def diff_cells(origin: List[str], destination: List[str]) -> List[CodeDiffHunk]:
        offset_diff = 0

        def _get_new_index(origin_index):
            """
            Known the index of an element in the initial_diff_hunks, get the new index of the item in the new result
            diff_hunks.
            """
            return origin_index + offset_diff

        # Get the initial corresponding matched index from myre_diff.
        initial_diff_hunks = DiffAlgorithms.myre_diff(origin, destination).diff_hunks

        # Get add-remove groups between two matched_cell_groups and then refine the matches of add-remove groups.
        from_idx = 0
        to_idx = 0
        add_hunks: List[str] = []
        remove_hunks: List[str] = []
        diff_hunks = initial_diff_hunks.copy()
        for i in range(len(initial_diff_hunks)):
            if initial_diff_hunks[i].option == "Both":
                if len(add_hunks) > 0 and len(remove_hunks) > 0:
                    # get the corresponding matched hunks from edr_diff of the add_remove groups
                    refined_hunks = DiffAlgorithms.edr_diff(origin=remove_hunks, destination=add_hunks).diff_hunks
                    # replace the add_remove groups with edr_diff result
                    diff_hunks[_get_new_index(from_idx) : _get_new_index(to_idx) + 1] = refined_hunks
                    offset_diff += len(refined_hunks) - (to_idx - from_idx + 1)

                # try to find the next group of add-remove
                add_hunks.clear()
                remove_hunks.clear()  # replace the add_remove groups with edr_diff result
                from_idx = i + 1
                to_idx = from_idx
            elif initial_diff_hunks[i].option == "Destination_only":
                add_hunks.append(initial_diff_hunks[i].content)
                to_idx = i
            elif initial_diff_hunks[i].option == "Origin_only":
                remove_hunks.append(initial_diff_hunks[i].content)
                to_idx = i
        if len(add_hunks) > 0 and len(remove_hunks) > 0:
            # get the corresponding matched hunks from edr_diff of the add_remove groups
            refined_hunks = DiffAlgorithms.edr_diff(origin=remove_hunks, destination=add_hunks).diff_hunks
            # replace the add_remove groups with edr_diff result
            diff_hunks[_get_new_index(from_idx) : _get_new_index(to_idx) + 1] = refined_hunks
            offset_diff += len(refined_hunks) - (to_idx - from_idx + 1)

        return diff_hunks

    @staticmethod
    def diff_variables(origin: Dict[str, str], destination: Dict[str, str]) -> List[VariableVersionCompare]:
        return [
            KishuDiff._compare_variable_value(name, origin.get(name, None), destination.get(name, None))
            for name in set(origin.keys()) | set(destination.keys())
        ]

    @staticmethod
    def _compare_variable_value(
        var_name: str, origin_val: Optional[str], destination_val: Optional[str]
    ) -> VariableVersionCompare:
        if origin_val is None:
            return VariableVersionCompare(var_name, "destination_only")
        if destination_val is None:
            return VariableVersionCompare(var_name, "origin_only")
        if origin_val == destination_val:
            return VariableVersionCompare(var_name, "both_same_version")
        else:
            return VariableVersionCompare(var_name, "both_different_version")
