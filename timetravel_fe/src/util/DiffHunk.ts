export interface DiffHunk {
    option: string;
    content: string;
    subDiffHunks?: DiffHunk[];
}