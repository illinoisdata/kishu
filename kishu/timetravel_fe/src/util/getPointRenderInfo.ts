// Commits[] to PointRenderer[]

import { PointRenderInfo } from "./PointRenderInfo";
import { Commit } from "./Commit";
import MinHeap from "heap-js";
import { COLORSPAN, COMMITHEIGHT, LINESPACING } from "./GraphSizeConsts";
//input Commits[], return a map of commit ID to PointRenderer(cx,cy, color)
export function getPointRenderInfos(commits: Commit[]): {
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

  //recycled x coordinates
  const recycleXs = new MinHeap<number>();

  //fist y
  let y = COMMITHEIGHT / 2;
  let maxX = LINESPACING / 2; //max new x coordinate to be assigned

  //result
  let pointRenderers = new Map<string, PointRenderInfo>();

  //traverse commits from newest to oldest to assign coordinates
  for (let i = 0; i < commits.length; i++) {
    let commit = commits[i];
    let parentOid = commit.parentOid;
    let parentIndex = commitIDIndex.get(parentOid);
    cy[i] = y;
    y += COMMITHEIGHT;
    //if cx hasn't been assigned, it means he is a leaf, assign cx first
    if (cx[i] == -1) {
      if (recycleXs.length > 0) {
        cx[i] = recycleXs.pop()!;
      } else {
        cx[i] = maxX;
        maxX += LINESPACING;
      }
    }
    //deal with the parent of cx, and judge if the x coordinate of cx can be recycled
    if (parentIndex === undefined || cx[parentIndex] !== -1) {
      //parent doesn't exist, or parent has been assigned, need to recycle cx's coordinate
      recycleXs.push(cx[i]);
    } else {
      cx[parentIndex] = cx[i];
    }

    //add to result
    pointRenderers.set(commit.oid, {
      color: COLORSPAN[getXaxisIndex(cx[i]) % COLORSPAN.length],
      cx: cx[i],
      cy: cy[i],
    });
  }
  return { info: pointRenderers, maxX: maxX, maxY: y };
}

function getXaxisIndex(cx: number): number {
  return Math.floor((cx - LINESPACING / 2) / LINESPACING);
}
