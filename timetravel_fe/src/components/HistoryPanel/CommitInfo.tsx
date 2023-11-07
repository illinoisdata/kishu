// input PointRenderer, return a info box
import {PointRenderInfo} from "../../util/PointRenderInfo";
import "./commitInfo.css";
import {Commit} from "../../util/Commit";
import {
    TagOutlined,
    ForkOutlined,
    FieldTimeOutlined,
    DownOutlined
} from "@ant-design/icons";
import {AppContext} from "../../App";
import {useContext} from "react";

export interface CommitInfoProps {
    commit: Commit;
    pointRendererInfo: PointRenderInfo;
    onclick: any;
    onContextMenu: any;
    newDay: string;
}

export function CommitInfo(props: CommitInfoProps) {
    const appContext = useContext(AppContext);

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
        <div>
            <FieldTimeOutlined/> {props.commit.timestamp.substring(0, 19)}
        </div>

    return (
        <div
            className={"commitInfo"}
            onClick={props.onclick}
            onContextMenu={props.onContextMenu}
        >
            {props.newDay !== "" ? (
                <div className={"newDay"}>
                    <DownOutlined />  {props.newDay}
                </div>
            ) : (
                <div className="empty-line"></div>
            )}
            {props.commit.branchIds.length !== 0 || props.commit.tags.length!=0 ? (
                <div className={"same_row"}>{_tags}{_branches} </div>
            ) : (
               _timestamp
            )}
        </div>
    );
}
