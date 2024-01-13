import {PointRenderInfo} from "../../util/PointRenderInfo";
import {COMMITHEIGHT} from "./GraphConsts";
import React from "react";
import "./historyPanel.css";

export interface FilterHighlightsProps {
    pointRenderInfos: Map<string, PointRenderInfo>;
    highlightedPointsIds: string[]|undefined;
}

function _FilterHighlights({pointRenderInfos, highlightedPointsIds}: FilterHighlightsProps) {
    const highlightTops = highlightedPointsIds?.map((commitID) => {
        return pointRenderInfos.get(commitID)?.cy! - COMMITHEIGHT / 2;
    })
    const filter_highlights = highlightTops?.map(highlightTop => {
        return <div className={"highlight filter-highlight"} style={{top: `${highlightTop}px`}}></div>
    })
    return (
        <>
            {filter_highlights}
        </>
    )
}

export const FilterHighlights = React.memo(_FilterHighlights);