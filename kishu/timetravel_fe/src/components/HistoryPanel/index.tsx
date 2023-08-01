/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 13:46:16
 * @LastEditTime: 2023-08-01 13:21:53
 * @FilePath: /src/components/HistoryPanel/index.tsx
 * @Description:
 */
// import HistoryPoint from "../HistoryPoint";
import { Gitgraph, Mode, Branch } from "@gitgraph/react";
import { History } from "../../util/History";
import { ReactSVGElement, useEffect, useState } from "react";
import { message } from "antd";
import ContextMenu from "./ContextMenu";
import TagEditor from "./TagEditor";
import { BackEndAPI } from "../../util/API";
export interface HistoryTreeProps {
  selectedHistoryID: string | undefined;
  histories: History[] | undefined;
  setHistories: any;
  setSelectedHistory: any;
  setSelectedHistoryID: any;
  showAll: boolean; //if false, show only tags
}

//This function is to generate a random new key for the GitGraph everytime a props is changed.
//To refresh the gitgraph when props are changed,
// the key of the GitGraph must also be changed, or the gitgraph.js
// will ignore the props' changes.

function HistoryTree({
  selectedHistoryID,
  histories,
  setHistories,
  setSelectedHistory,
  setSelectedHistoryID,
}: HistoryTreeProps) {
  let branches = new Map<string, Branch>();
  useEffect(() => {
    return () => branches.clear();
  });

  const [contextMenuPosition, setContextMenuPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  //context menu for the history tree
  const handleContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    setContextMenuPosition({ x: event.clientX, y: event.clientY });
  };
  const handleCloseContextMenu = () => {
    setContextMenuPosition(null);
  };
  async function handleSubmit(newTag: string) {
    await BackEndAPI.setTag(selectedHistoryID!, newTag);
    const data = await BackEndAPI.getInitialData();
    setHistories(data!);
  }

  return (
    <div onContextMenu={handleContextMenu} onClick={handleCloseContextMenu}>
      <Gitgraph key={Date.now()} options={{ mode: Mode.Compact }}>
        {(gitgraph) => {
          // console.log("try to rerender");
          // console.log(selectedHistoryID);
          for (let element of histories!) {
            if (!branches.has(element.branchId)) {
              if (element.parentBranchID === "-1") {
                branches.set(
                  element.branchId,
                  gitgraph.branch(element.branchId.toString())
                );
              } else {
                branches.set(
                  element.branchId,
                  branches
                    .get(element.parentBranchID)!
                    .branch(element.branchId.toString())
                );
              }
            }
            if (element.oid !== selectedHistoryID) {
              branches.get(element.branchId)!.commit({
                subject: element.oid.toString(),
                onClick(commit) {
                  // alert("clicked");
                  // props.setSelectedHistory(element);
                  // setSelectedHistoryID(element.oid);
                  setSelectedHistoryID(element.oid);
                },
                tag: element.tag,
              });
            } else {
              branches.get(element.branchId)!.commit({
                subject: "select me" + element.oid.toString(),
                dotText: "🙀",
                tag: element.tag,
              });
            }
          }
        }}
      </Gitgraph>
      {contextMenuPosition && (
        <ContextMenu
          x={contextMenuPosition.x}
          y={contextMenuPosition.y}
          onClose={handleCloseContextMenu}
          setIsModalOpen={setIsModalOpen}
        />
      )}
      <TagEditor
        isModalOpen={isModalOpen}
        setIsModalOpen={setIsModalOpen}
        defaultContent={"abc"}
        submitHandler={undefined}
        selectedHistoryID={selectedHistoryID}
      ></TagEditor>
    </div>
  );
}

export default HistoryTree;
