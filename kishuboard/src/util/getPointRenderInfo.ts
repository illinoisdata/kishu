import {PointRenderInfo} from "./PointRenderInfo";
import {Commit} from "./Commit";
import {VisPoint, VisPointType} from "./VisPoint";
import MinHeap from "heap-js";
import {COLORSPAN, COMMITHEIGHT, DATEHEADERHEIGHT, LINESPACING} from "../components/HistoryPanel/GraphConsts";
import {extractDateFromString} from "./ExtractDateFromString";

export enum TopologyCommitType {
    LEAF,
    BRANCH,
    NEWDAY4BRANCH,//first commit of a new day for a branch
    ROOT,
    USERIMPL,//manual commit or has tag/branch
    MERGE,//"visually merge" commit, whose parent and nb_parent are different
    NORMAL,
    HEAD
}

export class VisInfoManager {
    commitIDIndex: Map<string, number>;//map from commit id to the index in time-sorted commits
    commits: Commit[];//time-sorted commits

    //group information
    commit2Group: Map<string, number>;
    group2Commits: Map<number, string[]>;
    maxGroupID: number;

    topologyCommitTypes: TopologyCommitType[];

    visPoints: VisPoint[];
    groupFolded: Map<number, boolean>;

    nbHead: string;
    varHead:string



    constructor(commits:Commit[], unfoldedGroup: number[] | undefined, nbHead:string, varHead:string){
        //a map from commit ID to the index in time-sorted commits， so that we can quickly find out the parent
        this.commitIDIndex = new Map<string, number>();
        for (let i = 0; i < commits.length; i++) {
            this.commitIDIndex.set(commits[i].oid, i);
        }
        this.commits = commits;
        this.nbHead = nbHead;
        this.varHead = varHead;

        this.commit2Group = new Map<string, number>();
        this.group2Commits = new Map<number, string[]>();
        this.maxGroupID = 0;
        this.topologyCommitTypes = new Array(this.commits.length).fill(TopologyCommitType.NORMAL);

        this.visPoints = [];

        this.calGroupInfo();
        this.groupFolded = new Map<number, boolean>();
        for (let i = 0; i <= this.maxGroupID; i++) {
            this.groupFolded.set(i, true);
            if(unfoldedGroup && unfoldedGroup.includes(i)){
                this.groupFolded.set(i, false);
            }
            else{
                this.groupFolded.set(i, true);
            }
        }
    }

    public getGroupInfo(){
        return {commit2Group: this.commit2Group, group2commit: this.group2Commits, maxGroupID: this.maxGroupID};
    }

    public getTopologyType(){
        return this.topologyCommitTypes;
    }

    public getVisPoints(isGroupFolded?:Map<number, boolean>):VisPoint[]{
        if (isGroupFolded){
            this.groupFolded = isGroupFolded!;
        }
        let groupAdded:boolean[] = new Array(this.maxGroupID).fill(false);
        this.visPoints = [];
        this.commits.forEach((commit, idx) => {
            let group = this.commit2Group.get(commit.oid)!
            if(this.group2Commits.get(group)!.length == 1 || !this.groupFolded.get(group)){
                //group is visible or single element group, not fold.
                this.visPoints.push({groupID: group, type: this.group2Commits.get(group)!.length == 1?VisPointType.SINGLE:VisPointType.GROUP_UNFOLE, visPointID: commit.oid, commit: commit, parentID: commit.parentOid, nbParentID: commit.nbParentOid});
            }else if(!groupAdded[group]){
                //group is folded
                const lastCommitIDOfGroup = this.group2Commits.get(group)![this.group2Commits.get(group)!.length - 1];
                const lastCommitOfGroup = this.commits[this.commitIDIndex.get(lastCommitIDOfGroup)!];
                this.visPoints.push({groupID: group, type: VisPointType.GROUP_FOLD, visPointID: commit.oid, commit: commit, parentID: lastCommitOfGroup.parentOid, nbParentID: lastCommitOfGroup.nbParentOid});
            }
            groupAdded[group] = true;
        })
        return this.visPoints;
    }

    public getVisPointID(commitID:string):string{
        if(!this.groupFolded){
            throw("visPoints is not calculated yet")
        }
        const groupID = this.commit2Group.get(commitID);
        if(groupID === undefined){
            throw("commitID not found")
        }
        // if the group is not folded, return the commitID itself
        if(!this.groupFolded.get(groupID)!){
            return commitID;
        }
        //if the group is folded, return the first commit id of the group
        return this.group2Commits.get(groupID)![0];
    }

    public getVisPoint(commitID:string){
        const pointID = this.getVisPointID(commitID);
        return this.visPoints.filter(point => point.visPointID === pointID)[0];
    }


    //***************helper functions for group assignment****************
    calGroupInfo(){
        //get the commit type for each commit
        let visited:boolean[] = new Array(this.commits.length).fill(false);
        for(let idx = 0; idx < this.commits.length; idx++){
            if(visited[idx]){
                continue;
            }
            //assign commit type to a new branch
            this.assTopoType2Branch(idx, visited);
        }
        this.topologyCommitTypes[this.commits.length - 1] = TopologyCommitType.ROOT;
        console.log(this.topologyCommitTypes)

        //get the group information based on commit type
        visited = new Array(this.commits.length).fill(false);
        this.maxGroupID = 0;
        for(let idx = 0; idx < this.commits.length; idx++){
            if(visited[idx]){
                continue;
            }
            // if(this.topologyCommitTypes[idx] === TopologyCommitType.LEAF){
                this.assGroup2Branch(idx, visited);
            // }
        }
        console.log(this.group2Commits)
    }

    containsDigitsPattern(input: string): boolean {
        const regex = /\[\d+\]/;
        return regex.test(input);
    }

    /**
     * assign topology commit type to a branch of commits
     * @param start_idx the index of the leaf commit of the branch
     * @param visited a boolean array to record whether a commit has been visited
     * @param topologyCommitTypes an array to record the topology commit type of each commit
     */
    assTopoType2Branch(start_idx:number, visited:boolean[]){
        this.topologyCommitTypes[start_idx] = TopologyCommitType.LEAF; //leaf is visible
        visited[start_idx] = true;
        let idx = this.commitIDIndex.get(this.commits[start_idx].parentOid);
        let prev_idx = start_idx;
        while(idx !== undefined && !visited[idx]){
            visited[idx] = true;
            //If it's a manual commit or has tag/branch, it's visible
            if(this.commits[idx].tags.length > 0 || this.commits[idx].branchIds.length > 0 || !this.containsDigitsPattern(this.commits[idx].message)){
                this.topologyCommitTypes[idx] = TopologyCommitType.USERIMPL;
            }
            //if it's the first commit for a branch of the new day, it's visible
            if(extractDateFromString(this.commits[idx].timestamp) !== extractDateFromString(this.commits[prev_idx].timestamp)){
                this.topologyCommitTypes[idx] = TopologyCommitType.NEWDAY4BRANCH;
            }
            //if it's a merge commit, it's visible
            if(this.commits[idx].parentOid !== this.commits[idx].nbParentOid){
                this.topologyCommitTypes[idx] = TopologyCommitType.MERGE;
                //the nb parent of a merged commit should also be visible
                if(this.commits[idx].nbParentOid!= undefined){
                    this.topologyCommitTypes[this.commitIDIndex.get(this.commits[idx].nbParentOid)!] = TopologyCommitType.BRANCH;
                }
            }
            //if it's code head or variable head, it's visible
            if(this.commits[idx].oid == this.nbHead || this.commits[idx].oid == this.varHead){
                this.topologyCommitTypes[idx] = TopologyCommitType.HEAD;
            }
            prev_idx = idx
            idx = this.commitIDIndex.get(this.commits[idx].parentOid)
        }
        if(idx){
            //meaning idx is a visited node by other branch, which means it's a branch node
            this.topologyCommitTypes[idx] = TopologyCommitType.BRANCH;
        }
    }

    /**
     * assign group information to a branch of commits
     * @param leaf the index of the leaf commit of the branch
     * @param visited a boolean array to record whether a commit has been visited
     * @param topologyCommitTypes an array to record the topology commit type of each commit, which is used to determine
     * how to group commits together
     */
    assGroup2Branch(leaf:number, visited:boolean[]){
        //the leaf can form a new group itself
        this.formSingleElementGroup(this.maxGroupID, this.commits[leaf].oid)
        let currentGroupMembers:string[] = [];
        let idx = this.commitIDIndex.get(this.commits[leaf].parentOid);
        while(idx !== undefined && !visited[idx]){
            visited[idx] = true;
            if(this.topologyCommitTypes[idx] === TopologyCommitType.NORMAL){
                currentGroupMembers.push(this.commits[idx].oid);
                this.commit2Group.set(this.commits[idx].oid, this.maxGroupID);
            }else{
                if(currentGroupMembers.length > 0){
                    //push the currentGroup into the group2Commits
                    this.group2Commits.set(this.maxGroupID, [...currentGroupMembers]);
                    currentGroupMembers = [];
                    //start a new group
                    this.maxGroupID ++;
                }
                //add the current node to the new group
                this.formSingleElementGroup(this.maxGroupID, this.commits[idx].oid);
            }
            //renew idx
            idx = this.commitIDIndex.get(this.commits[idx].parentOid);
        }
        //push the last currentGroup into the group2Commits
        if(currentGroupMembers.length > 0){
            this.group2Commits.set(this.maxGroupID, [...currentGroupMembers]);
            this.maxGroupID ++;
        }
    }

    /**
     * form a single element group and increase the maxGroupID by 1
     * @param groupID
     * @param commitID
     */
    formSingleElementGroup(groupID:number, commitID:string){
        this.group2Commits.set(this.maxGroupID, [commitID]);
        this.commit2Group.set(commitID, this.maxGroupID);
        this.maxGroupID++;
    }
}

export class RenderInfoCalculator {
    pointID2Index: Map<string, number>;
    visPoints: VisPoint[];
    isDateFolded: Map<string, boolean> | undefined;

    //the render infos to be calculated
    cx: number[];
    cy: number[];
    isFoldedByDate: boolean[]; //whether the group is folded by date
    maxX: number;
    maxY: number;
    visPointID2RenderInfo: Map<string, PointRenderInfo>;
    messagePosition: number[]; //the x position of message for group i
    constructor(visPoints:VisPoint[], isDateFolded:Map<string, boolean> | undefined){
        //a map from commit ID to the index in time-sorted commits， so that we can quickly find out the parent
        this.pointID2Index = new Map<string, number>();
        for (let i = 0; i < visPoints.length; i++) {
            this.pointID2Index.set(visPoints[i].visPointID, i);
        }

        this.visPoints = visPoints;

        this.isDateFolded = isDateFolded;

        //coordinates to be calculated
        this.cx = new Array(visPoints.length).fill(-1);
        this.cy = new Array(visPoints.length).fill(-1);
        this.messagePosition = new Array(visPoints.length).fill(-1);

        this.isFoldedByDate = new Array(visPoints.length).fill(false)
        this.maxX = LINESPACING / 2;
        this.maxY = 0;
        this.visPointID2RenderInfo = new Map<string, PointRenderInfo>();
    }

    public getPointRenderInfo():{
        info: Map<string, PointRenderInfo>;
        maxX: number;
        maxY: number;
        messagePosition: number[];
    }{
        this.assignY();
        this.assignX();
        return {info: this.visPointID2RenderInfo, maxX: this.maxX, maxY: this.maxY, messagePosition: this.messagePosition};
    }


    //***************helper functions for render_info(position,color) calculation****************
    /**
     * assign the x coordinate to a branch of commits
     * @param from the first index of visCommits of the branch
     * @param to the last index of visCommits of the branch
     * @param value the x coordinate of the branch
     */
    setMessagePosition(from:number,to:number,value:number){
        for(let i = from; i <= to; i++){
            this.messagePosition[i] = value > this.messagePosition[i]?value:this.messagePosition[i];
        }
    }

    //assign x coordinate to a branch, return the parent of the branch
    /**
     * assign x coordinate to a branch of visCommit, return the index of the parent of the branch
     * @param startIdx the index of the branch in visCommits
     * @param x the x coordinate to be assigned to the branch
     */
    assignX2Branch(startIdx:number,x:number):number|undefined{
        let idx:number | undefined = startIdx;
        while(idx!== undefined && this.cx[idx] === -1){
            this.cx[idx] = x;
            this.visPointID2RenderInfo.set(this.visPoints[idx].visPointID, {
                color: COLORSPAN[this.getXaxisIndex(this.cx[idx]) % COLORSPAN.length],
                cx: this.cx[idx],
                cy: this.cy[idx],
                folded: this.isFoldedByDate[idx],
            });
            idx = this.pointID2Index.get(this.visPoints[idx].parentID);
        }
        this.setMessagePosition(startIdx, idx?idx:this.visPoints.length - 1, x);
        return idx;
    }

    /**
     * find a feasible x coordinate for a commit
     * @param y the y coordinate of the first commit of a branch
     * @param recycleXs the recycled x coordinates
     */
    findFeasibleX(y:number, recycleXs:MinHeap<[number,number]>):number{
        //helper variables
        let possible_column: number, min_y: number;
        let findCycledColumnFlag = false;
        let result:number = -1;

        findCycledColumnFlag = false;
        if (recycleXs.length > 0) {
            let unqualified_recycled_x:[number,number][] = [];
            while (recycleXs.length > 0) {
                [possible_column, min_y] = recycleXs.pop()!;
                if (y < min_y) {
                    //unqualified
                    unqualified_recycled_x.push([possible_column, min_y]);
                }else{
                    result = possible_column;
                    findCycledColumnFlag = true;
                    break;
                }
            }
            //put the unqualified recycled x back
            for (let j = 0; j < unqualified_recycled_x.length; j++) {
                recycleXs.push(unqualified_recycled_x[j]);
            }
        }
        if (!findCycledColumnFlag) {
            result = this.maxX;
            this.maxX += LINESPACING;
        }
        return result;
    }

    /**
     * assign y coordinates to render_commits
     */
    assignY(){
        let y = COMMITHEIGHT / 2;
        //traverse commits to assign y coordinates and consider folding
        for (let i = 0; i < this.visPoints.length; i++) {
            //if commits[i] start a new day, increase y to give the time header a slot
            if (i == 0 || extractDateFromString(this.visPoints[i].commit.timestamp) !== extractDateFromString(this.visPoints[i - 1].commit.timestamp)) {
                y += DATEHEADERHEIGHT;
            }
            if(!this.isDateFolded || !this.isDateFolded.get(extractDateFromString(this.visPoints[i].commit.timestamp))){
                // if the current commit is not folded
                this.cy[i] = y;
                y += COMMITHEIGHT;
                this.isFoldedByDate[i] = false;
            }
            else{
                // if the current commit is folded, assign its y coordinate to the previous y slot(the time header's y slot)
                this.cy[i] = y - COMMITHEIGHT/2 - DATEHEADERHEIGHT/2;
                this.isFoldedByDate[i] = true;
            }
        }
        this.maxY = y;
    }

    /**
     * assign x coordinates to render_commits
     */
    assignX(){
        //recycled x coordinates
        const recycleXs = new MinHeap<[number, number]>(); //[x, min_y], means when x is recycled and the y of the to-be-put commit is less than or equal to min_y, then you can put the commit here.
        for(let i = 0; i < this.visPoints.length; i ++){
            if(this.cx[i] == -1){
                let x = this.findFeasibleX(this.cy[i], recycleXs);
                let last_id = this.assignX2Branch(i, x);
                recycleXs.push([x, last_id?this.cy[last_id]:Number.POSITIVE_INFINITY]);
            }
        }

    }


    /**
     * given a coordinate, get the x-slot index
     * @param cx x coordinate
     */
    getXaxisIndex(cx: number): number {
        return Math.floor((cx - LINESPACING / 2) / LINESPACING);
    }


}






