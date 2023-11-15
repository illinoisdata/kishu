import {Commit} from "../../util/Commit";
import React, {
    useContext,
    useMemo,
    useState,
} from "react";
import ContextMenu from "./ContextMenu";
import {AppContext} from "../../App";
import {HistoryGraph} from "./HistoryGraph";
import {getPointRenderInfos} from "../../util/getPointRenderInfo";
import "./historyPanel.css";
import {PointRenderInfo} from "../../util/PointRenderInfo";
import {COMMITHEIGHT} from "./GraphConsts";
import {CommitInfos} from "./CommitInfos";
import {FilterHighlights} from "./FilterHighlights";

export interface HistoryPanelProps {
    highlighted_commit_ids: string[];
}

function HistoryPanel({highlighted_commit_ids}: HistoryPanelProps) {
    const props = useContext(AppContext);

    //state for graph
    const [pointRenderInfos, setPointRenderInfos] = useState<
        Map<string, PointRenderInfo>
    >(new Map());
    const [commitIDMap, setCommitIDMap] = useState<Map<string, Commit>>(new Map());
    const [svgMaxX, setsvgMaxX] = useState<number>(0);
    const [svgMaxY, setsvgMaxY] = useState<number>(0);


    //status of pop-ups
    const [contextMenuPosition, setContextMenuPosition] = useState<{
        x: number;
        y: number;
    } | null>(null);


    function handleCloseContextMenu() {
        setContextMenuPosition(null);
    }


    //update display information of the graph and highlight
    useMemo(() => {
        let infos = getPointRenderInfos(props?.commits!);
        setPointRenderInfos(infos["info"]);
        setsvgMaxX(infos["maxX"]);
        setsvgMaxY(infos["maxY"]);
        let _commitIDMap = new Map<string, Commit>();
        props?.commits.forEach((commit) => _commitIDMap.set(commit.oid, commit));
        setCommitIDMap(_commitIDMap)
    }, [props?.commits]);
    const highlightTop = pointRenderInfos.get(props?.selectedCommitID!)?.cy! - COMMITHEIGHT / 2;


    return (
        <div className="historyPanel" onClick={handleCloseContextMenu}>
            <HistoryGraph
                Commits={commitIDMap}
                pointRendererInfos={pointRenderInfos}
                currentCommitID={props?.currentHeadID!}
                svgMaxX={svgMaxX}
                svgMaxY={svgMaxY}
            />
            <CommitInfos pointRenderInfos={pointRenderInfos} setContextMenuPosition={setContextMenuPosition}
                         commits={props!.commits} setSelectedCommitID={props!.setSelectedCommitID}
                         setSelectedBranchID={props?.setSelectedBranchID}/>
            <div className={"highlight select-highlight"} style={{top: `${highlightTop}px`}}></div>
            <FilterHighlights pointRenderInfos={pointRenderInfos} highlighted_commit_ids={highlighted_commit_ids}/>

            {contextMenuPosition && (
                <ContextMenu
                    x={contextMenuPosition.x}
                    y={contextMenuPosition.y}
                    onClose={handleCloseContextMenu}
                />
            )}
        </div>
    );
}

export default HistoryPanel;