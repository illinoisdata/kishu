// input PointRenderer, return a info box
import {PointRenderInfo} from "../../util/PointRenderInfo";
import "./Info.css";
import {Commit} from "../../util/Commit";
import {
    TagOutlined,
    ForkOutlined,
    FieldTimeOutlined,
    DownOutlined
} from "@ant-design/icons";
import React from "react";
import {extractTimeFromString} from "../../util/ExtractDateFromString";

export interface SingleCommitInfoProps {
    commit: Commit;
    onclick: any;
    onContextMenu: any;
}

function _SingleCommitInfo(props: SingleCommitInfoProps) {

    const _tags = props.commit.tags?.map((tag) => {
        return (
            <span className={"tag_name"}>
        {" "}
                <TagOutlined/> <span>{tag}</span>{" "}
      </span>
        );
    });

    const _branches = props.commit.branchIds?.map((branch) => {
        return (
            <span className={"branch_name"}>
                <ForkOutlined/> <span>{branch}</span>{" "}
            </span>
        );
    });

    const _timestamp =
        <div className={"timestamp"}>
            {extractTimeFromString(props.commit.timestamp)}
        </div>

    return (
        <div
            className={"commitInfo"}
            onClick={props.onclick}
            onContextMenu={props.onContextMenu}
        >
            <div className={"empty-line"}></div>
            {props.commit.branchIds.length !== 0 || props.commit.tags.length !== 0 ? (
                <div className={"tags_container"}>{_tags}{_branches} </div>
            ) : (
                _timestamp
            )}
        </div>
    );
}

export const SingleCommitInfo = React.memo(_SingleCommitInfo);
