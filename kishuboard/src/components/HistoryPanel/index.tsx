import {Commit} from "../../util/Commit";
import {VisPoint, VisPointType} from "../../util/VisPoint";
import React, {useContext, useEffect, useMemo, useState,} from "react";
import ContextMenu from "./ContextMenu";
import {AppContext} from "../../App";
import {HistoryGraph} from "./HistoryGraph";
import {RenderInfoCalculator, VisInfoManager} from "../../util/getPointRenderInfo";
import "./historyPanel.css";
import {PointRenderInfo} from "../../util/PointRenderInfo";
import {COMMITHEIGHT} from "./GraphConsts";
import {Infos} from "./Infos";
import {FilterHighlights} from "./FilterHighlights";
import {extractDateFromString} from "../../util/ExtractDateFromString";

export interface HistoryPanelProps {
    highlighted_commit_ids: string[];
    refreshGraphHandler: any;
    width:number;
    scrollSignal: boolean;
    scrollableHisPanel: any;
}

export interface RenderPoint {
    commit: Commit;
    isDummy: boolean;
    isGroupFolded: boolean;
}

export function HistoryPanel({highlighted_commit_ids, refreshGraphHandler, width, scrollSignal, scrollableHisPanel}: HistoryPanelProps) {
    const props = useContext(AppContext);

    //state for date-folded
    const [isDateFolded, setIsDateFolded] = useState<Map<string, boolean> | undefined>(undefined);
    const [dateCommitNumebr, setDateCommitNumber] = useState<Map<string, number> | undefined>(undefined)

    //state for group-folded
    const [unFoldedGroup, setUnfoldedGroup] = useState<number[] | undefined>(undefined);

    // //state for info panel, renderPoints also include dummy points
    // const [renderPoints, setRenderPoints] = useState<RenderPoint[]>([]);

    //status of pop-ups
    const [contextMenuPosition, setContextMenuPosition] = useState<{
        x: number;
        y: number;
    } | null>(null);

    const visInfoManager = new VisInfoManager(props!.commits,unFoldedGroup,props!.nbHeadID!,props!.currentHeadID!);
    const visPoints = visInfoManager.getVisPoints();
    const visPointRenderInfos = new RenderInfoCalculator(visPoints,isDateFolded).getPointRenderInfo();
    const svgMaxX = visPointRenderInfos.maxX;
    const svgMaxY = visPointRenderInfos.maxY;
    const svgMessagePosition = visPointRenderInfos.messagePosition;
    //define render_commits (insert dummy commits to commits and delete the commits that is folded) makes the render logic of commit info easier
    const renderPoints: RenderPoint[] = [];
    visPoints.forEach((point,index) => {
        //if the commit is a new date, create a dummy commit
        if(index === 0 || extractDateFromString(point.commit.timestamp) !== extractDateFromString(visPoints[index - 1].commit.timestamp)){
            renderPoints.push({commit: point.commit, isDummy: true, isGroupFolded: point.type === VisPointType.GROUP_FOLD});
        }
        // if the commit is not folded, add it to renderCommits
        if(!isDateFolded || !isDateFolded.get(extractDateFromString(point.commit.timestamp))){
            renderPoints.push({commit: point.commit, isDummy: false, isGroupFolded: point.type === VisPointType.GROUP_FOLD});
        }
    })

    function handleCloseContextMenu() {
        setContextMenuPosition(null);
    }

    //every time the commits change, refresh the is group folded info and date-commit number mapping
    useMemo(() => {
        //refresh date commit number
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
        );
        setDateCommitNumber(newDateCommitNumer)
        setUnfoldedGroup(undefined)
        },[props?.commits]
    )


    useEffect(() => {
        if(!highlightedTops){
            return;
        }else{
            scrollableHisPanel.current?.scrollTo({top:highlightedTops, behavior: "smooth"})
        }
    },[scrollSignal]
    )
    //visInfoManager haven't been updated yet. Some time we need to wait until it is updated(commits changed), other time don't(only the select changed)
    const selectVisPointID = visInfoManager?.getVisPointID(props?.selectedCommitID!);
    const currentPointID = visInfoManager?.getVisPointID(props?.diffDestCommitID?props?.diffDestCommitID:props?.currentHeadID!);
    const selectTop = selectVisPointID?visPointRenderInfos.info.get(selectVisPointID)?.cy! - COMMITHEIGHT / 2:undefined;
    const currentTop = currentPointID?visPointRenderInfos.info.get(currentPointID)?.cy! - COMMITHEIGHT / 2:undefined;
    // const highlightedTops = visInfoManager?highlighted_commit_ids.length > 0?visPointRenderInfos.info.get(visInfoManager.getVisPointID(highlighted_commit_ids[0]))?.cy! - COMMITHEIGHT / 2:undefined:undefined;
    const firstHighlight = highlighted_commit_ids.map(id => visInfoManager.getVisPointID(id)).filter(point => point !== undefined)[0]
    const highlightedTops = visInfoManager?firstHighlight?visPointRenderInfos.info.get(firstHighlight)?.cy! - COMMITHEIGHT / 2:undefined:undefined;

    const visPointMap: Map<string, {point:VisPoint,idx:number}> = new Map()
    visPoints.forEach((point,index) => {
        visPointMap.set(point.visPointID,{point:point,idx:index})
    })
    return (
        <div className = "historyPanel">
        <div className="historyGraph" onClick={handleCloseContextMenu}>
            <HistoryGraph
                visPoints={visPointMap}
                pointRendererInfos={visPointRenderInfos.info}
                currentVarID={visInfoManager?.getVisPointID(props?.currentHeadID!)}
                currentCodeID={visInfoManager?.getVisPointID(props?.nbHeadID!)}
                svgMaxX={svgMaxX}
                svgMaxY={svgMaxY}
                svgMessagePosition={svgMessagePosition}
                selectedPointID={visInfoManager?.getVisPointID(props?.selectedCommitID!)}
                setUnfoldedGroup={setUnfoldedGroup}
                unfoldedGroup={unFoldedGroup}
            />
            <Infos setContextMenuPosition={setContextMenuPosition}
                   renderPoints={renderPoints} setSelectedCommitID={props!.setSelectedCommitID}
                   setSelectedBranchID={props?.setSelectedBranchID} isDateFolded={isDateFolded} setIsDateFolded={setIsDateFolded} dateCommitNumber={dateCommitNumebr}/>
            {!props?.diffDestCommitID && <div className={"highlight select-highlight"} style={{top: `${selectTop}px`}}></div>}
            <FilterHighlights pointRenderInfos={visPointRenderInfos.info} highlightedPointsIds={visInfoManager?highlighted_commit_ids.map((commit_id) => visInfoManager!.getVisPointID(commit_id)):undefined} visInfoManager={visInfoManager}/>
            {props?.diffDestCommitID && (
                <div className={"highlight select-highlight "} style={{top: `${currentTop}px`}}> <div className={"diff-notation"}> <div className={"diff-to"}>Destination</div></div> </div>)}
            {props?.diffDestCommitID && (
                <div className={"highlight select-highlight "} style={{top: `${selectTop}px`}}> <div className={"diff-notation"}> <div className={"diff-from"}>Source</div></div> </div>)
            }
            {contextMenuPosition && (
                <ContextMenu
                    x={contextMenuPosition.x}
                    y={contextMenuPosition.y}
                    onClose={handleCloseContextMenu}
                    refreshGraphHandler={refreshGraphHandler}
                />
            )}
        </div>
        <div className="hint" style={{width:`calc(${width}% - 2px)`}}>Press ctrl to multi select and diff two commits</div>
        </div>
    );
}