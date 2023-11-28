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
import {Infos} from "./Infos";
import {FilterHighlights} from "./FilterHighlights";
import {extractDateFromString} from "../../util/ExtractDateFromString";

export interface HistoryPanelProps {
    highlighted_commit_ids: string[];
}

export interface RenderCommit {
    commit: Commit;
    isDummy: boolean;
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

    //state for fold
    const [isDateFolded, setIsDateFolded] = useState<Map<string, boolean> | undefined>(undefined);

    //state for info panel
    const [renderCommits, setRenderCommits] = useState<RenderCommit[]>([]);

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
        let infos = getPointRenderInfos(props?.commits!,isDateFolded);
        setPointRenderInfos(infos["info"]);
        setsvgMaxX(infos["maxX"]);
        setsvgMaxY(infos["maxY"]);

        let _commitIDMap = new Map<string, Commit>();
        props?.commits.forEach((commit) => _commitIDMap.set(commit.oid, commit));
        setCommitIDMap(_commitIDMap)

    }, [props?.commits, isDateFolded]);

    useMemo(() => {
        //define render_commits (insert dummy commits to commits and delete the commits that is folded) makes the render logic of commit info easier
        let _renderCommits: RenderCommit[] = [];
        props?.commits.forEach((commit,index) => {
            //if the commit is a new date, create a dummy commit
            if(index === 0 || extractDateFromString(commit.timestamp) !== extractDateFromString(props?.commits[index-1].timestamp)){
                _renderCommits.push({commit: commit, isDummy: true});
            }
            // if the commit is not folded, add it to renderCommits
            if(!isDateFolded || !isDateFolded.get(extractDateFromString(commit.timestamp))){
                _renderCommits.push({commit: commit, isDummy: false});
            }
        })
        setRenderCommits(_renderCommits)
    },[props?.commits, isDateFolded] );

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
            <Infos setContextMenuPosition={setContextMenuPosition}
                   renderCommits={renderCommits} setSelectedCommitID={props!.setSelectedCommitID}
                   setSelectedBranchID={props?.setSelectedBranchID} isDateFolded={isDateFolded} setIsDateFolded={setIsDateFolded}/>
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