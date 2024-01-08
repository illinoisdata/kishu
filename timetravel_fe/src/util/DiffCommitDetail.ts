import {DiffCodeHunk, DiffVarHunk} from "./DiffHunk";


export interface DiffCodeDetail {
    notebookCellDiffHunks: DiffCodeHunk[];
    executedCellDiffHunks: DiffCodeHunk[];
}