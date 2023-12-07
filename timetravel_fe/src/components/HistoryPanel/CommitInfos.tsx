import {Commit} from "../../util/Commit";
import React from "react";
import {PointRenderInfo} from "../../util/PointRenderInfo";
import {SingleCommitInfo} from "./SingleCommitInfo";
import "./CommitInfos.css"

export interface CommitInfoPanelProps {
    pointRenderInfos: Map<string, PointRenderInfo>;
    setContextMenuPosition: any;
    commits: Commit[];
    setSelectedCommitID: any;
    setSelectedBranchID: any;
}

function _CommitInfos(props: CommitInfoPanelProps) {
    const commitInfos = props.commits.map((commit, index) => {
        let newDay: string
        if (index === 0 || commit.timestamp.substring(0, 10) !== props.commits[index - 1].timestamp.substring(0, 10)) {
            newDay = commit.timestamp.substring(0, 10);
        } else {
            newDay = "";
        }
        return (
            <SingleCommitInfo
                newDay={newDay}
                commit={commit}
                pointRendererInfo={props.pointRenderInfos.get(commit.oid)!}
                onclick={() => {
                    props.setSelectedCommitID(commit.oid);
                    props.setSelectedBranchID("");
                }}
                onContextMenu={(event: React.MouseEvent) => {
                    event.preventDefault();
                    props.setSelectedCommitID(commit.oid);
                    props.setSelectedBranchID("");
                    props.setContextMenuPosition({x: event.clientX, y: event.clientY});
                }}
            />
        );
    })
    return (
        <div className={"commitInfosContainer"}>{commitInfos}</div>
    )
}

export const CommitInfos = React.memo(_CommitInfos);