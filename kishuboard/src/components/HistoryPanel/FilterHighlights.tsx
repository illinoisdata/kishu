import {PointRenderInfo} from "../../util/PointRenderInfo";
import {COMMITHEIGHT} from "./GraphConsts";
import React from "react";
import "./historyPanel.css";
import {VisPoint, VisPointType} from "../../util/VisPoint";
import {VisInfoManager} from "../../util/getPointRenderInfo";

export interface FilterHighlightsProps {
    pointRenderInfos: Map<string, PointRenderInfo>;
    highlightedPointsIds: (string | undefined)[]|undefined;
    visInfoManager: VisInfoManager;
}

function _FilterHighlights({pointRenderInfos, highlightedPointsIds, visInfoManager}: FilterHighlightsProps) {
    highlightedPointsIds = highlightedPointsIds?.filter(id => id!== undefined)
    const highlightTops = highlightedPointsIds?.map((commitID) => {
        return pointRenderInfos.get(commitID as string)?.cy! - COMMITHEIGHT / 2;
    })
    const filter_highlights = highlightTops?.map((highlightTop,idx) => {
        // let visPoint = visInfoManager.getVisPoint(highlightedPointsIds![idx])
        if(visInfoManager.getVisPoint(highlightedPointsIds![idx] as string).type === VisPointType.GROUP_FOLD){
            return <div className={"highlight filter-highlight-group"} style={{top: `${highlightTop}px`}}></div>
        }
        return <div className={"highlight filter-highlight"} style={{top: `${highlightTop}px`}}></div>
    })
    return (
        <>
            {filter_highlights}
        </>
    )
}

export const FilterHighlights = React.memo(_FilterHighlights);