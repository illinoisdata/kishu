import {DiffCodeHunk} from "./DiffHunk";


export interface DiffCodeDetail {
    notebookCellDiffHunks: DiffCodeHunk[];
    executedCellDiffHunks: DiffCodeHunk[];
}