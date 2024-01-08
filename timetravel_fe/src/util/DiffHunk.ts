
import {VersionChange} from "./VariableVersionCompare";
import {Variable} from "./Variable";

export interface DiffCodeHunk {
    option: string;
    content: string;
    subDiffHunks?: DiffCodeHunk[];
}

export interface DiffVarHunk {
    option: number;
    content: Variable;
}