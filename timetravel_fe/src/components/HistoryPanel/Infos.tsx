import {Commit} from "../../util/Commit";
import React from "react";
import {PointRenderInfo} from "../../util/PointRenderInfo";
import {SingleCommitInfo} from "./SingleCommitInfo";
import "./CommitInfos.css"
import {RenderCommit} from "./index";
import {SingleNewDateHeaderInfo} from "./SingleNewDateHeaderInfo";
import {extractDateFromString} from "../../util/ExtractDateFromString";
import {COMMITHEIGHT} from "./GraphConsts";

export interface CommitInfoPanelProps {
    setContextMenuPosition: any;
    renderCommits: RenderCommit[];
    setSelectedCommitID: any;
    setSelectedBranchID: any;
    setIsDateFolded: any;
    isDateFolded?: Map<string, boolean>;
}

function _CommitInfos(props: CommitInfoPanelProps) {
    const commitInfos = props.renderCommits.map((renderCommit, index) => {
        return (
            <>
                {!renderCommit.isDummy && <SingleCommitInfo
                    commit={renderCommit.commit}
                    onclick={() => {
                        props.setSelectedCommitID(renderCommit.commit.oid);
                        props.setSelectedBranchID("");
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
    const headerInfos = props.renderCommits.map((renderCommit, index) => {
        if (renderCommit.isDummy) {
            return (
                <SingleNewDateHeaderInfo
                    newDate={extractDateFromString(renderCommit.commit.timestamp)}
                    setIsDateFolded={props.setIsDateFolded}
                    isDateFolded={props.isDateFolded}
                    y_position={index * COMMITHEIGHT}
                />
            )
        }
        return null;
    })
    return (
        <>
            <div className={"commitInfosContainer"}>{commitInfos}</div>
            {headerInfos}
        </>

    )
}

export const Infos = React.memo(_CommitInfos);