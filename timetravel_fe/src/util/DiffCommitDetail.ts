import {DiffHunk} from "./DiffHunk";


export interface DiffCommitDetail {
    notebookCellDiffHunks: DiffHunk[];
    executedCellDiffHunks: DiffHunk[];
}