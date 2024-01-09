// Commits[] to PointRenderer[]

import {PointRenderInfo} from "./PointRenderInfo";
import {Commit} from "./Commit";
import MinHeap from "heap-js";
import {COLORSPAN, COMMITHEIGHT, DATEHEADERHEIGHT, LINESPACING} from "../components/HistoryPanel/GraphConsts";
import {extractDateFromString} from "./ExtractDateFromString";

//input Commits[], return a map of commit ID to PointRenderer(cx,cy, color)
export function getPointRenderInfos(commits: Commit[], isDateFolded: Map<string, boolean> | undefined): {
    info: Map<string, PointRenderInfo>;
    maxX: number;
    maxY: number;
} {
    //a map from commit ID to the index in time-sorted commits
    let commitIDIndex = new Map<string, number>();
    for (let i = 0; i < commits.length; i++) {
        commitIDIndex.set(commits[i].oid, i);
    }

    //coordinates to be calculated
    let cx: number[] = new Array(commits.length).fill(-1);
    let cy: number[] = new Array(commits.length).fill(-1);

    //whether the commit is folded
    let isCommitFolded: boolean[] = new Array(commits.length).fill(false);

    //recycled x coordinates
    const recycleXs = new MinHeap<[number, number]>(); //[x, min_y], means when x is recycled and the y of the to-be-put commit is less than or equal to min_y, then you can put the commit here.

    //fist y and x
    let y = COMMITHEIGHT / 2;
    let maxX = LINESPACING / 2; //max new x coordinate to be assigned

    //result
    let pointRenderers = new Map<string, PointRenderInfo>();

    //traverse commits to assign y coordinates without considering folding
    for (let i = 0; i < commits.length; i++) {
        //if commits[i] start a new day, increase y to give the time header a slot
        if (i == 0 || extractDateFromString(commits[i].timestamp) !== extractDateFromString(commits[i - 1].timestamp)) {
            y += DATEHEADERHEIGHT;
        }
        if(!isDateFolded || !isDateFolded.get(extractDateFromString(commits[i].timestamp))){
            // if the current commit is not folded
            cy[i] = y;
            y += COMMITHEIGHT;
            isCommitFolded[i] = false;
        }
        else{
            // if the current commit is folded, assign its y coordinate to the previous y slot(the time header's y slot)
            cy[i] = y - COMMITHEIGHT/2 - DATEHEADERHEIGHT/2;
            isCommitFolded[i] = true;
        }
    }

    //helper variables
    let possible_column: number, min_y: number;
    let findCycledColumnFlag = false;

    //traverse commits from newest to oldest to assign coordinates
    for (let i = 0; i < commits.length; i++) {
        let commit = commits[i];
        let parentOid = commit.parentOid;
        let parentIndex = commitIDIndex.get(parentOid);
        //if cx hasn't been assigned, it means he is a leaf, assign cx first
        if (cx[i] === -1) {
            findCycledColumnFlag = false;
            if (recycleXs.length > 0) {
                let unqualified_recycled_x:[number,number][] = [];
                while (recycleXs.length > 0) {
                    [possible_column, min_y] = recycleXs.pop()!;
                    if (cy[i] < min_y) {
                        //unqualified
                        unqualified_recycled_x.push([possible_column, min_y]);
                    }else{
                        cx[i] = possible_column;
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
                cx[i] = maxX;
                maxX += LINESPACING;
            }
        }
        //deal with the parent of cx, and judge if the x coordinate of cx can be recycled
        if (parentIndex === undefined || cx[parentIndex] !== -1) {
            //parent doesn't exist, or parent has been assigned, need to recycle cx's coordinate
            if(parentIndex){
                recycleXs.push([cx[i],cy[parentIndex]]);
            }else{
                recycleXs.push([cx[i],0]);
            }
        } else {
            cx[parentIndex] = cx[i];
        }

        //add to result
        pointRenderers.set(commit.oid, {
            color: COLORSPAN[getXaxisIndex(cx[i]) % COLORSPAN.length],
            cx: cx[i],
            cy: cy[i],
            folded: isCommitFolded[i],
        });
    }
    return {info: pointRenderers, maxX: maxX, maxY: y};
}

function getXaxisIndex(cx: number): number {
    return Math.floor((cx - LINESPACING / 2) / LINESPACING);
}
