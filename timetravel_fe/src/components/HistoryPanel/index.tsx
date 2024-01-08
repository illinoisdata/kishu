import {Commit} from "../../util/Commit";
import React, {
    useContext, useEffect,
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
import {DoubleLeftOutlined} from "@ant-design/icons";

export interface HistoryPanelProps {
    highlighted_commit_ids: string[];
}

export interface RenderCommit {
    commit: Commit;
    isDummy: boolean;
}

export function HistoryPanel({highlighted_commit_ids}: HistoryPanelProps) {
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
    const [dateCommitNumebr, setDateCommitNumber] = useState<Map<string, number> | undefined>(undefined)

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

    useMemo(() => {
        let newDateCommitNumer: Map<string,number> = new Map()
        props!.commits.forEach(
            commit => {
                let date = extractDateFromString(commit.timestamp)
                if (newDateCommitNumer.has(date)){
                    newDateCommitNumer.set(date,newDateCommitNumer.get(date)! + 1)
                }else{
                    newDateCommitNumer.set(date,1)
                }
            }

                // let date = extractDateFromString(commit.timestamp)
                // if (newDateCommitNumer.has(key)) {
                //     // If the key exists, increment the value
                //     const currentValue = map.get(key);
                //     if (currentValue !== undefined) {
                //         map.set(key, currentValue + 1);
                //     }
                // } else {
                //     // If the key doesn't exist, set the value to 1
                //     map.set(key, 1);
                // }
                // newDateCommitNumer.get(extractDateFromString(commit.timestamp))
                // newDateCommitNumer.set(extractDateFromString(commit.timestamp))
        );
        setDateCommitNumber(newDateCommitNumer)
        },[props?.commits]

    )


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

    const selectTop = pointRenderInfos.get(props?.selectedCommitID!)?.cy! - COMMITHEIGHT / 2;
    const currentTop = pointRenderInfos.get(props?.diffDestCommitID?props?.diffDestCommitID:props?.currentHeadID!)?.cy! - COMMITHEIGHT / 2;


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
                   setSelectedBranchID={props?.setSelectedBranchID} isDateFolded={isDateFolded} setIsDateFolded={setIsDateFolded} dateCommitNumber={dateCommitNumebr}/>
            {!props?.inDiffMode && <div className={"highlight select-highlight"} style={{top: `${selectTop}px`}}></div>}
            <FilterHighlights pointRenderInfos={pointRenderInfos} highlighted_commit_ids={highlighted_commit_ids}/>
            {props?.inDiffMode && (
                <div className={"highlight select-highlight "} style={{top: `${currentTop}px`}}> <div className={"diff-notation"}> <DoubleLeftOutlined/>Destination</div>  </div>)}
            {props?.inDiffMode && (
                <div className={"highlight select-highlight "} style={{top: `${selectTop}px`}}> <div className={"diff-notation"}> <DoubleLeftOutlined/>Source</div> </div>)
            }


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