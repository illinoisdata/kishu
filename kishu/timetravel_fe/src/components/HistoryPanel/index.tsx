/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 13:46:16
 * @LastEditTime: 2023-08-01 13:21:53
 * @FilePath: /src/components/HistoryPanel/index.tsx
 * @Description:
 */
// import HistoryPoint from "../HistoryPoint";
import {
  Gitgraph,
  Mode,
  Branch,
  templateExtend,
  TemplateName,
  CommitOptions,
} from "@gitgraph/react";
import { History } from "../../util/History";
import React, { ReactSVGElement, useEffect, useMemo, useState } from "react";
import { message } from "antd";
import ContextMenu from "./ContextMenu";
import TagEditor from "./TagEditor";
import { BackEndAPI } from "../../util/API";
import { Judger } from "../../util/JudgeFunctions";
import { ReactSvgElement } from "@gitgraph/react/lib/types";

export interface HistoryTreeProps {
  selectedHistoryID: string | undefined;
  histories: History[] | undefined;
  setHistories: any;
  setSelectedHistory: any;
  setSelectedHistoryID: any;
}

function HistoryTree({
  selectedHistoryID,
  histories,
  setHistories,
  setSelectedHistory,
  setSelectedHistoryID,
}: HistoryTreeProps) {
  //************states*************** */
  const [judgeShowFunctionID, setJudgeShowFunctionID] = useState(1); //0:show only histories with tags, 1: show all histories, 2: show only selected histories
  const [groups, setGroups] = useState<Map<string, History[]>>(); // are the folded groups(Map<headOID, foldedGroupInfo>)
  const [isGroupFolded, setIsGroupFolded] = useState<Map<string, boolean>>(); //<group header's OID, isGroupFolded>
  const [groupIndex, setGroupIndex] = useState<Map<string, string>>(); //<history oid, group head's oid>
  //the context menu will show after right click
  const [contextMenuPosition, setContextMenuPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  // the Modal will show after user choose to change the tag for the selected history
  const [isModalOpen, setIsModalOpen] = useState(false);

  //**********************helper functions***********/
  function judgeGrouped(history: History) {
    if (judgeShowFunctionID === 0) {
      return Judger.JudgeGroupByTag(history);
    } else if (judgeShowFunctionID === 1) {
      return Judger.JudgeGroupByNoGroup(history);
    } else {
      return Judger.JudgeGroupBySearch(history);
    }
  }
  function findParent(child: History): History | null {
    if (child.parentOid === "-1") {
      return null;
    }
    return histories!.filter((his) => his.oid === child.parentOid)[0];
  }
  function handleContextMenu(event: React.MouseEvent) {
    event.preventDefault();
    setContextMenuPosition({ x: event.clientX, y: event.clientY });
  }
  function handleCloseContextMenu() {
    setContextMenuPosition(null);
  }
  var renderDot = function (commit: any) {
    return React.createElement(
      "svg",
      {
        xmlns: "http://www.w3.org/2000/svg",
        viewBox: "0 0 71.84 75.33",
        height: "30",
        width: "30",
      },
      React.createElement(
        "g",
        { fill: commit.style.dot.color, stroke: "white", strokeWidth: "2" },
        React.createElement("path", {
          d: "M68.91,35.38c4.08-1.15,3.81-3-.22-3.75-3.1-.7-18.24-5.75-20.71-6.74-2.15-1-4.67-.12-1,3.4,4,3.53,1.36,8.13,2.79,13.47C50.6,44.89,52.06,49,56,55.62c2.09,3.48,1.39,6.58-1.42,6.82-1.25.28-3.39-1.33-3.33-3.82h0L44.68,43.79c1.79-1.1,2.68-3,2-4.65s-2.5-2.29-4.46-1.93l-1.92-4.36a3.79,3.79,0,0,0,1.59-4.34c-.62-1.53-2.44-2.27-4.37-2L36,22.91c1.65-1.12,2.46-3,1.83-4.52a3.85,3.85,0,0,0-4.37-1.95c-.76-1.68-2.95-6.89-4.89-10.73C26.45,1.3,20.61-2,16.47,1.36c-5.09,4.24-1.46,9-6.86,12.92l2.05,5.35a18.58,18.58,0,0,0,2.54-2.12c1.93-2.14,3.28-6.46,3.28-6.46s1-4,2.2-.57c1.48,3.15,16.59,47.14,16.59,47.14a1,1,0,0,0,0,.11c.37,1.48,5.13,19,19.78,17.52,4.38-.52,6-1.1,9.14-3.83,3.49-2.71,5.75-6.08,5.91-12.62.12-4.67-6.22-12.62-5.81-17S66.71,36,68.91,35.38Z",
        }),
        React.createElement("path", {
          d: "M2.25,14.53A28.46,28.46,0,0,1,0,17.28s3,4.75,9.58,3a47.72,47.72,0,0,0-1.43-5A10.94,10.94,0,0,1,2.25,14.53Z",
        })
      )
    );
  };
  function addCommitToGraph(
    element: History,
    text?: string,
    ClickHandler?: string
  ) {
    if (!text) {
      //not ""+" or "-"
      if (element.oid !== selectedHistoryID) {
        branches.get(element.branchId)!.commit({
          subject: element.oid.toString(),
          onClick(commit) {
            setSelectedHistoryID(element.oid);
          },
          tag: element.tag,
          renderDot(commit) {
            // const svgProps: React.SVGProps<SVGSVGElement> = {
            //   width: 20,
            //   height: 20,
            //   viewBox: "0 0 200 200",
            // };

            return (
              <svg
                // {...svgProps}
                onContextMenu={(event) => {
                  message.info("right clicked");
                  setSelectedHistoryID(element.oid);
                }}
                onClick={(event) => {
                  message.info("left clicked");
                  setSelectedHistoryID(element.oid);
                }}
                // onClick={setSelectedHistoryID(element.oid)}
              >
                <circle
                  id={commit.hash}
                  cx={commit.style.dot.size}
                  cy={commit.style.dot.size}
                  r={commit.style.dot.size}
                  fill={commit.style.dot.color as string}
                />
              </svg>
            );
          },
        });
      } else {
        branches.get(element.branchId)!.commit({
          subject: "select me" + element.oid.toString(),
          dotText: "🐞",
          tag: element.tag,
        });
      }
    } else if (text === "➕") {
      branches.get(element.branchId)!.commit({
        subject: element.oid.toString(),
        dotText: text!,
        style: {
          dot: {
            color: "grey",
            size: 10,
          },
        },
        onClick(commit) {
          const gOID = groupIndex!.get(element.oid);
          setIsGroupFolded((previous) => {
            let newMap = new Map(previous);
            newMap.set(gOID!, false);
            return newMap;
          });
        },
      });
    } else {
      branches.get(element.branchId)!.commit({
        subject: element.oid.toString(),
        dotText: text!,
        style: {
          dot: {
            color: "grey",
            size: 12,
          },
        },
        onClick(commit) {
          const gOID = groupIndex!.get(element.oid);
          setIsGroupFolded((previous) => {
            let newMap = new Map(previous);
            newMap.set(gOID!, true);
            return newMap;
          });
        },
      });
    }
  }
  async function handleTagSubmit(newTag: string) {
    const data = await BackEndAPI.setTag(selectedHistoryID!, newTag);
    // const data = await BackEndAPI.getInitialData();
    setHistories(data!);
  }

  //**************Variables that are recreated per render*/
  //all the branches of GitGraph
  let branches = new Map<string, Branch>();

  //initialize groups that are logically folded together, reinitialize when histories are changed, or
  //visibility type is changed.
  useMemo(() => {
    let newGroups = new Map<string, History[]>();
    let newGroupIndex = new Map<string, string>();
    let newIsGroupFolded = new Map<string, boolean>();
    let tmpBranchFolderHead = new Map<string, string>(); //remember current branch's folded group's head
    for (let element of histories!) {
      if (judgeGrouped(element)) {
        let parent = findParent(element);
        if (parent?.branchId !== element.branchId || !judgeGrouped(parent)) {
          //the element is head of a group
          newGroups.set(element.oid, [element]);
          newGroupIndex.set(element.oid, element.oid);
          newIsGroupFolded.set(element.oid, true);
          tmpBranchFolderHead.set(element.branchId, element.oid);
        } else {
          //find the header and input to the fold
          let headerOID = tmpBranchFolderHead.get(element.branchId);
          newGroups.get(headerOID!)!.push(element);
          newGroupIndex.set(element.oid, headerOID!);
        }
      }
    }
    setGroups(newGroups);
    setGroupIndex(newGroupIndex);
    setIsGroupFolded(newIsGroupFolded);
  }, [histories, judgeShowFunctionID]);

  return (
    <div onContextMenu={handleContextMenu} onClick={handleCloseContextMenu}>
      {/* To refresh the gitgraph when props are changed, the key of the
      GitGraph must also be changed, or the gitgraph.js will ignore the
      props' changes. */}
      <Gitgraph
        key={Date.now()}
        options={{
          mode: Mode.Compact,
          template: templateExtend(TemplateName.Metro, {
            colors: ["#FFCC66", "#CCCC66", "#FF00CC", "#6633CC", "#999900"],
          }),
        }}
      >
        {(gitgraph) => {
          for (let element of histories!) {
            //if history belongs to a new branch, create a the on the parent branch
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
            if (!judgeGrouped(element)) {
              addCommitToGraph(element);
            } else {
              //find the group
              let groupOID = groupIndex!.get(element.oid);
              if (isGroupFolded!.get(groupOID!)) {
                //group is folded
                //judge if it's the head
                if (groupOID === element.oid) {
                  addCommitToGraph(element, "➕");
                }
              } else {
                //group is unfolded
                let currentGroup = groups!.get(groupOID!);
                //judge if it's head
                if (groupOID === element.oid) {
                  addCommitToGraph(element, "➖");
                }
                addCommitToGraph(element);
                //judge if it's tail
                if (
                  currentGroup![currentGroup!.length - 1].oid == element.oid
                ) {
                  addCommitToGraph(currentGroup![0], "➖");
                } else {
                }
              }
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
          setJudgeFunctionID={setJudgeShowFunctionID}
          setIsGroupFolded={setIsGroupFolded}
          judgeFunctionID={judgeShowFunctionID}
          isGroupFolded={isGroupFolded}
        />
      )}
      <TagEditor
        isModalOpen={isModalOpen}
        setIsModalOpen={setIsModalOpen}
        defaultContent={"abc"}
        submitHandler={handleTagSubmit}
        selectedHistoryID={selectedHistoryID}
      ></TagEditor>
    </div>
  );
}

React.createElement("svg");
export default HistoryTree;
