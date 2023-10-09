// input PointRenderer, return a info box
import { PointRenderInfo } from "../../util/PointRenderInfo";
import "./commitInfo.css";
import { Commit } from "../../util/Commit";
import {
  TagOutlined,
  ForkOutlined,
  FieldTimeOutlined,
} from "@ant-design/icons";
import { AppContext } from "../../App";
import { useContext } from "react";

export interface CommitInfoProps {
  commit: Commit;
  pointRendererInfo: PointRenderInfo;
  onclick: any;
  onContextMenu: any;
}

export function CommitInfo(props: CommitInfoProps) {
  const appContext = useContext(AppContext);
  const _tags = props.commit.tags?.map((tag) => {
    return (
      <span className={"tag_name"}>
        {" "}
        <TagOutlined /> <span>{tag}</span>{" "}
      </span>
    );
  });

  const _branches = props.commit.branchIds?.map((branch) => {
    return (
      <span className={"branch_name"}>
        {" "}
        <ForkOutlined /> <span>{branch}</span>{" "}
      </span>
    );
  });
  return (
    <div
      className={
        props.commit.oid == appContext?.selectedCommitID
          ? "selected_commitInfo"
          : "commitInfo"
      }
      onClick={props.onclick}
      onContextMenu={props.onContextMenu}
    >
      {props.commit.tags.length !== 0 ? (
        <div className={"same_row"}>{_tags}</div>
      ) : (
        <div>
          {" "}
          <FieldTimeOutlined /> {props.commit.timestamp}
        </div>
      )}
      {props.commit.branchIds.length !== 0 ? (
        <div className={"same_row"}>{_branches}</div>
      ) : (
        <div className="empty-line"></div>
      )}
    </div>
  );
}
