from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiffHunk:
    option: str  # origin_only, destination_only, both
    content: str  # if option is both, but contents of origin and destination is similar but not same, then it will
    # show the content of the origin
    sub_diff_hunks: Optional[List[
        DiffHunk]]  # if two similar cells are matched, then sub_diff_hunks will be the line-level Diff-hunk list
    # inside the matched cell


@dataclass
class DiffAlgorithmResult:
    origin_same_idx: List[int]  # origin_same_idx[3] = 5 means origin[3] matches destination[5]
    destination_same_idx: List[int]
    diff_hunks: List[DiffHunk]
    similarity: float  # the similarity score between the two series


class DiffAlgorithms:

    @staticmethod
    def myre_diff(origin: List[str], destination: List[str]) -> DiffAlgorithmResult:
        """
           An implementation of the Myers diff algorithm.
           See http://www.xmailserver.org/diff2.pdf

           @return : list1[3] = 5, means that series1[0] = series2[5],
                        list2[3] = 5, means that series2[3] = series1[5]
        """
        Frontier = namedtuple('Frontier', ['x', 'history', 'same_idxs', 'matched_num'])

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
                go_down = (k == -d or
                           (k != d and frontier[k - 1].x < frontier[k + 1].x))

                # Figure out the starting point of this iteration. The diagonal
                # offsets come from the geometry of the edit grid - if you're going
                # down, your diagonal is lower, and if you're going right, your
                # diagonal is higher.
                if go_down:
                    old_x, history, same_idxs, matched_num = frontier[k + 1]
                    x = old_x
                else:
                    old_x, history, same_idxs, matched_num = frontier[k - 1]
                    x = old_x + 1

                # We want to avoid modifying the old history, since some other step
                # may decide to use it.
                history = history[:]
                same_idxs = same_idxs[:]
                y = x - k

                # We start at the invalid point (0, 0) - we should only start building
                # up history when we move off of it.
                if 1 <= y <= b_max and go_down:
                    history.append(DiffHunk("Destination_only", destination[one(y)], sub_diff_hunks=None))
                elif 1 <= x <= a_max:
                    history.append(DiffHunk("Origin_only", origin[one(x)], sub_diff_hunks=None))

                # Chew up as many diagonal moves as we can - these correspond to common lines,
                # and they're considered "free" by the algorithm because we want to maximize
                # the number of these in the output.
                while x < a_max and y < b_max and origin[one(x + 1)] == destination[one(y + 1)]:
                    x += 1
                    y += 1
                    history.append(DiffHunk("Both", origin[one(x)], sub_diff_hunks=None))
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
                    return DiffAlgorithmResult(series1_common, series2_common, history, similarity)

                else:
                    frontier[k] = Frontier(x, history, same_idxs, matched_num)
        return DiffAlgorithmResult([], [], [], 0)

    @staticmethod
    def edr_diff(origin: List[str], destination: List[str], threshold=0.5) -> DiffAlgorithmResult:
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
        edr_matrix = [[float('inf')] * (n + 1) for _ in range(m + 1)]

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
                if (i == 2 and j == 3):
                    print("debug")
                myre = DiffAlgorithms.myre_diff(origin[i - 1].split("\n"), destination[j - 1].split("\n"))
                if myre.similarity < threshold:
                    cost = float('inf')  # never regard as similar
                else:
                    cost = 1 - myre.similarity  # the more similar, the less cost of edit
                edr_matrix[i][j] = min((cost + edr_matrix[i - 1][j - 1]),  # match
                                       (1 + edr_matrix[i][j - 1]),  # insertion
                                       (1 + edr_matrix[i - 1][j]))  # deletion
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
        i = 0
        for i in range(m):
            if origin_same_idx[i] == -1:
                diff_hunks.append(DiffHunk("Origin_only", origin[i], sub_diff_hunks=None))
            else:
                to = origin_same_idx[i]
                for k in range(j, to):
                    diff_hunks.append(DiffHunk("Destination_only", destination[k], sub_diff_hunks=None))
                line_level_myre = DiffAlgorithms.myre_diff(origin[i].split("\n"), destination[to].split("\n"))
                if (abs(line_level_myre.similarity - 1) < 1e-9):
                    line_diff_hunks = None
                else:
                    line_diff_hunks = line_level_myre.diff_hunks
                diff_hunks.append(DiffHunk("Both", origin[i], sub_diff_hunks=line_diff_hunks))
                # if line level diff only contains both, then we should not add this diff hunk, meaning they are the same
                j = to + 1
        for k in range(j, n):
            diff_hunks.append(DiffHunk("Destination_only", destination[k], sub_diff_hunks=None))
        return DiffAlgorithmResult(origin_same_idx, destination_same_idx, diff_hunks, similarity)
