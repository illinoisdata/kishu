
import React, {useContext} from "react";
import {SingleCommitInfo} from "./SingleCommitInfo";
import "./CommitInfos.css"
import {RenderPoint} from "./index";
import {SingleNewDateHeaderInfo} from "./SingleNewDateHeaderInfo";
import {extractDateFromString} from "../../util/ExtractDateFromString";
import {COMMITHEIGHT, DATEHEADERHEIGHT} from "./GraphConsts";
import {AppContext} from "../../App";

export interface CommitInfoPanelProps {
    setContextMenuPosition: any;
    renderPoints: RenderPoint[];
    setSelectedCommitID: any;
    setSelectedBranchID: any;
    setIsDateFolded: any;
    dateCommitNumber: Map<string,number> | undefined
    isDateFolded?: Map<string, boolean>;
}

function _CommitInfos(props: CommitInfoPanelProps) {
    const appProps = useContext(AppContext);
    const handleClick = (commitId: string, ctrlPressed: boolean) => {
        console.log(ctrlPressed)
        if(ctrlPressed && appProps?.selectedCommit){
            appProps?.setDiffDestCommitID(commitId);
        }else{
            appProps?.setSelectedCommitID(commitId);
            appProps?.setDiffDestCommitID(undefined);
            props.setSelectedBranchID("");
        }
    }

    const commitInfos = props.renderPoints.map((renderCommit, index) => {
        return (
            <>
                {!renderCommit.isDummy && <SingleCommitInfo
                    commit={renderCommit.commit}
                    onclick={(e: React.MouseEvent) => {
                        e.preventDefault()
                        handleClick(renderCommit.commit.oid, e.metaKey || e.ctrlKey)
                    }}
                    onContextMenu={(event: React.MouseEvent) => {
                        event.preventDefault();
                        props.setSelectedCommitID(renderCommit.commit.oid);
                        props.setSelectedBranchID("");
                        props.setContextMenuPosition({x: event.clientX, y: event.clientY});
                    }}
                />}
                {
                    renderCommit.isDummy &&
                    <div className={"empty_info"}></div>
                }
            </>

        );
    })
    let dateHeaderPositions: [string, number][] = [];
    let dummyNumber = 0;
    let commitNumber = 0;
    props.renderPoints.forEach((renderCommit) => {
        if (renderCommit.isDummy) {
            dateHeaderPositions.push([extractDateFromString(renderCommit.commit.timestamp), dummyNumber * DATEHEADERHEIGHT + commitNumber * COMMITHEIGHT + DATEHEADERHEIGHT / 2]);
            dummyNumber++;
        } else {
            commitNumber++;
        }
    })
    const headerInfos = dateHeaderPositions.map((value) => {
        return (
            <SingleNewDateHeaderInfo
                newDate={value[0]}
                commitNumber = {props.dateCommitNumber!.get(value[0])!}
                setIsDateFolded={props.setIsDateFolded}
                isDateFolded={props.isDateFolded}
                y_position={value[1] - DATEHEADERHEIGHT / 2}
            />)
    })
    return (
        <>
            <div className={"commitInfosContainer"}>{commitInfos}</div>
            {headerInfos}
        </>

    )
}

export const Infos = React.memo(_CommitInfos);