export interface Session{
    NotebookID: string;
    kernelID: string;
    notebookPath: string;
    isAlive: boolean;
}