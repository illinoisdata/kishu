import {Commit} from "./Commit";

export enum VisPointType {
    SINGLE,
    GROUP_FOLD,
    GROUP_UNFOLE
}

export interface VisPoint {
    type: VisPointType;
    groupID: number;
    visPointID: string; // if only one point, it's if it's group_fold, it's the commit id of the first commit in the group
    commit: Commit; // if it's group_fold, it's the first commit in the group
    parentID: string; //visPointID of the parent
}