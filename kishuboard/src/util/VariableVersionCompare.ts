export enum VersionChange{
    origin_only,
    destination_only,
    both_same_version,
    both_different_version
}
export interface VariableVersionCompare{
    variableName: string;
    option: string;
}