/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 13:46:16
 * @LastEditTime: 2023-07-18 13:06:13
 * @FilePath: /src/components/HistoryPanel/HistoryTree.tsx
 * @Description:
 */
// import HistoryPoint from "../HistoryPoint";
import { Gitgraph, Mode, Branch } from "@gitgraph/react";
import { History } from "../../util/History";
import { ReactSVGElement, useEffect, useState } from "react";
import { message } from "antd";
export interface HistoryTreeProps {
  selectedHistoryID: number | undefined;
  histories: History[] | undefined;
  setSelectedHistory: any;
  setSelectedHistoryID: any;
}

function HistoryTree({
  selectedHistoryID,
  histories,
  setSelectedHistory,
  setSelectedHistoryID,
}: HistoryTreeProps) {
  let branches = new Map<number, Branch>();
  useEffect(() => {
    return () => branches.clear();
  });
  return (
    <Gitgraph key={selectedHistoryID} options={{ mode: Mode.Compact }}>
      {(gitgraph) => {
        console.log("try to rerender");
        console.log(selectedHistoryID);
        for (let element of histories!) {
          if (!branches.has(element.branchId)) {
            if (element.parentBranchID === -1) {
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
            });
          } else {
            branches.get(element.branchId)!.commit({
              subject: "select me" + element.oid.toString(),
              dotText: "🙀",
              style: { color: "red" },
            });
          }
        }
      }}
    </Gitgraph>
  );
}

export default HistoryTree;
