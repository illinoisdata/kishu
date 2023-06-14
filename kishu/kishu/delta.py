"""
Delta from one state to another.
"""
from __future__ import annotations

import dill as pickle
from typing import List, Set, Tuple

from kishu.state import Cells, ContinuousPickler, Execution, SerializedCells, State


"""
Control flags/constants
"""
PRINT_CELL_SIZE = False


"""
StateDelta = List[ScopeCellsDelta], consisting of
- The differences from older scope cells to newer scope cells
- The newer execution states
"""
class ScopeCellsDelta:
    """
    Represent differences from a scope cell to another with WRITE and DELETE deltas.
    - WRITE: a cell is new or has changed.
    - DELETE: a cell is deleted.
    """

    def __init__(self, added: SerializedCells, deleted: Set[str], execution: Execution) -> None:
        self.added = added  # Added/overwrite cells.
        self.deleted = deleted  # Deleted cells.
        self.execution = execution  # Execution state
        
    @staticmethod
    def _from_to(
        from_cells: SerializedCells,
        to_cells: SerializedCells,
        execution: Execution,
    ) -> ScopeCellsDelta:
        """
        Find delta on a pair of cells.
        """
        # Extracted new cells or modified cells (WRITE).
        added = {}
        for key, to_cells_value in to_cells.items():
            if key not in from_cells or from_cells[key] != to_cells_value:
                added[key] = to_cells_value

        # Extract missing cells (DELETE).
        deleted = set(from_cells) - set(to_cells)

        return ScopeCellsDelta(
            added=added,
            deleted=deleted,
            execution=execution,
        )

    @staticmethod
    def _from_to_different(
        from_cells: SerializedCells,
        to_cells: SerializedCells,
        execution: Execution,
    ) -> ScopeCellsDelta:
        """
        Find delta on a pair of cells from totally different scopes.
        """
        return ScopeCellsDelta(
            added=to_cells,
            deleted=set(from_cells) - set(to_cells),
            execution=execution,
        )

    def get_added(self):
        return self.added

    def get_deleted(self):
        return self.deleted

    def get_execution(self):
        return self.execution

    def __repr__(self) -> str:
        if PRINT_CELL_SIZE:
            added_list = str([(key, len(value)) for key, value in self.added.items()])
        else:
            added_list = str(list(self.added))
        return 'ScopeCellsDelta(' \
            f'added= {added_list}, ' \
            f'deleted= {self.deleted}, ' \
            f'execution= {self.execution}' \
            f')'


class StateDelta:
    def __init__(self, scope_deltas: List[ScopeCellsDelta]) -> None:
        self.scope_deltas = scope_deltas

    @staticmethod
    def delta(from_state: State, to_state: State, same_frames: List[bool]) -> StateDelta:
        """
        Find delta on a pair of states
        """
        # TODO: reuse last extraction to extract only once per state.
        from_scope_state, _ = StateDelta._extract_scope_state(from_state)
        to_scope_state, to_executions = StateDelta._extract_scope_state(to_state)
        scope_deltas = StateDelta._delta_scope_state(
            from_scope_state=from_scope_state,
            to_scope_state=to_scope_state,
            to_executions=to_executions,
            same_frames=same_frames,
        )
        return StateDelta(scope_deltas=scope_deltas)

    @staticmethod
    def _extract_scope_state(state: State) -> Tuple[List[SerializedCells], List[Execution]]:
        # Use this pickler to combine share objects
        pickler = ContinuousPickler()

        # In reverse frame-key order to keep reference stable and so increase chance of equality.
        scope_state = []
        executions = []
        for frame in reversed(state.get_frames()):
            cells: Cells = frame.get_cells()
            execution: Execution = frame.get_execution()
            scope_state.append({key: pickler.dumps(cells[key]) for key in sorted(cells)})
            executions.append(execution)
        return scope_state[::-1], executions[::-1]

    @staticmethod
    def _delta_scope_state(
        from_scope_state: List[SerializedCells],
        to_scope_state: List[SerializedCells],
        to_executions: List[Execution],
        same_frames: List[bool],

    ) -> List[ScopeCellsDelta]:
        assert len(to_scope_state) == len(same_frames)
        assert len(same_frames) == 1 or all(
            same_frames[idx] and not same_frames[idx+1] for idx in range(len(same_frames)-1)
        )

        # Reverse frame order assuming base frame is at the end.
        from_scope_state = from_scope_state[::-1]
        to_scope_state = to_scope_state[::-1]
        same_frames = same_frames[::-1]

        # Iterate on common frames.
        diff = []
        for f_idx in range(len(to_scope_state)):
            from_scope_cells = {} if f_idx >= len(from_scope_state) else from_scope_state[f_idx]
            to_scope_cells = to_scope_state[f_idx]
            execution = to_executions[f_idx]
            same_frame = same_frames[f_idx]
            if same_frame:
                diff.append(ScopeCellsDelta._from_to(
                    from_cells=from_scope_cells,
                    to_cells=to_scope_cells,
                    execution=execution,
                ))
            else:
                diff.append(ScopeCellsDelta._from_to_different(
                    from_cells=from_scope_cells,
                    to_cells=to_scope_cells,
                    execution=execution,
                ))

        # Mark the rest of frames as deleted.
        for f_idx in range(len(to_scope_state), len(from_scope_state)):
            diff.append(ScopeCellsDelta._from_to_different(
                from_cells=from_scope_cells,
                to_cells={},
                execution=execution,
            ))

        # Flip frame order back.
        return diff[::-1]

    def get_scope_deltas(self):
        return self.scope_deltas

    def __repr__(self) -> str:
        scope_deltas_str = '\n'.join([scope_delta.__repr__() for scope_delta in self.scope_deltas])
        scope_deltas_str = scope_deltas_str.replace('\n', '\n\t')
        return f'StateDelta(\n\t{scope_deltas_str}\n)'
