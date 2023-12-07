import {PointRenderInfo} from "../../util/PointRenderInfo";
import {COMMITHEIGHT} from "./GraphConsts";
import React from "react";
import "./historyPanel.css";

export interface FilterHighlightsProps {
    pointRenderInfos: Map<string, PointRenderInfo>;
    highlighted_commit_ids: string[];
}

function _FilterHighlights({pointRenderInfos, highlighted_commit_ids}: FilterHighlightsProps) {
    const highlightTops = highlighted_commit_ids.map((commitID) => {
        return pointRenderInfos.get(commitID)?.cy! - COMMITHEIGHT / 2;
    })
    const filter_highlights = highlightTops.map(highlightTop => {
        return <div className={"highlight filter-highlight"} style={{top: `${highlightTop}px`}}></div>
    })
    return (
        <>
            {filter_highlights}
        </>
    )
}

export const FilterHighlights = React.memo(_FilterHighlights);