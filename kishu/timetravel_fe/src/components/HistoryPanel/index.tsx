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
import { Commit } from "../../util/Commit";
import React, {
  ReactSVGElement,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { message } from "antd";
import ContextMenu from "./ContextMenu";
import TagEditor from "./TagEditor";
import { BackEndAPI } from "../../util/API";
import { Judger } from "../../util/JudgeFunctions";
import { ReactSvgElement } from "@gitgraph/react/lib/types";
import { AppContext } from "../../App";
import { CheckoutWaitingModal } from "./CheckoutWaitingForModal";
import BranchNameEditor from "./BranchNameEditor";
import HoverPopup from "./HoverOverModal";

function HistoryTree() {
  const props = useContext(AppContext);
  console.log("rerender history tree again");

  //************states of history tree*************** */
  const [judgeShowFunctionID, setJudgeShowFunctionID] = useState(1); //0:show only histories with tags, 1: show all histories, 2: show only selected histories
  const [groups, setGroups] = useState<Map<string, Commit[]>>(); // are the folded groups(Map<headOID, foldedGroupInfo>)
  const [isGroupFolded, setIsGroupFolded] = useState<Map<string, boolean>>(); //<group header's OID, isGroupFolded>
  const [groupIndex, setGroupIndex] = useState<Map<string, string>>(); //<history oid, group head's oid>
  //********************************************************** */

  //********status of pop-ups************************ */
  const [contextMenuPosition, setContextMenuPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [isTagEditorOpen, setIsTagEditorOpen] = useState(false);
  const [isBranchNameEditorOpen, setIsBranchNameEditorOpen] = useState(false);
  const [isCheckoutWaitingModelOpen, setIsCheckoutWaitingModelOpen] =
    useState(false);
  const [waitingFor, setWaitingfor] = useState(""); //wait for what, like tag, checkout or XXX
  const [mouseOverPosition, setMouseOverPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [mouseOverTimestamp, setMouseOverTimestamp] = useState<string>("");
  //********************************************************************* */

  //**********************helper functions***********/
  function judgeGrouped(history: Commit) {
    if (judgeShowFunctionID === 0) {
      return Judger.JudgeGroupByTag(history);
    } else if (judgeShowFunctionID === 1) {
      return Judger.JudgeGroupByNoGroup(history);
    } else {
      return Judger.JudgeGroupBySearch(history);
    }
  }
  function findParent(child: Commit): Commit | null {
    if (child.parentOid === "-1") {
      return null;
    }
    return props!.commits!.filter((his) => his.oid === child.parentOid)[0];
  }
  function addCommitToGraph(
    element: Commit,
    text?: string,
    ClickHandler?: string
  ) {
    if (!text) {
      //not ""+" or "-"
      if (element.oid !== props!.selectedCommitID!) {
        branches.get(element.branchId)!.commit({
          subject: element.oid.toString(),
          tag: element.tag,
          renderDot(commit) {
            return (
              <svg
                // {...svgProps}
                onContextMenu={(event) => {
                  message.info("right clicked");
                  props!.setSelectedCommitID(element.oid);
                }}
                onClick={(event) => {
                  message.info("left clicked");
                  props!.setSelectedCommitID(element.oid);
                }}
                onMouseOver={(event) => {
                  handleMouseOverCommit(commit.x, commit.y, element.timestamp);
                }}
                onMouseOut={(event) => {
                  handleMouseOutCommit();
                }}
                // onClick={setSelectedHistoryID(element.oid)}
              >
                <circle
                  id={commit.hash}
                  cx={commit.style.dot.size}
                  cy={commit.style.dot.size}
                  r={commit.style.dot.size}
                  // fill={commit.style.dot.color as string}
                  fill={
                    element.oid! === props!.currentHeadID
                      ? "red"
                      : (commit.style.dot.color as string)
                  }
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
          onMouseOver(commit) {
            handleMouseOverCommit(commit.x, commit.y, element.timestamp);
          },
          onMouseOut(commit) {
            handleMouseOutCommit();
          },
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
  /************************************************************************** */

  //***********************event handelers************/
  function handleContextMenu(event: React.MouseEvent) {
    event.preventDefault();
    setContextMenuPosition({ x: event.clientX, y: event.clientY });
  }
  function handleMouseOverCommit(x: number, y: number, timestamp: string) {
    if (mouseOverPosition === null) {
      console.log("on_mouseOver");
      setMouseOverTimestamp(timestamp);
      setMouseOverPosition({ x: x + 100, y: y + 50 });
    }
  }
  function handleMouseOutCommit() {
    setMouseOverPosition(null);
  }
  function handleCloseContextMenu() {
    setContextMenuPosition(null);
  }
  async function handleTagSubmit(newTag: string) {
    try {
      await BackEndAPI.setTag(props!.selectedCommitID!!, newTag);
      const newGraph = await BackEndAPI.getCommitGraph();
      console.log(newGraph);
      props!.setCommits(newGraph.commits);
      props!.setBranchIDs(
        new Set(newGraph.commits.map((commit) => commit.branchId))
      );
      props!.setCurrentHeadID(newGraph.currentHead);
    } catch (error) {
      throw error;
    }
  }
  async function handleBranchNameSubmit(newBranchName: string) {
    try {
      await BackEndAPI.createBranch(props!.selectedCommitID!, newBranchName);
      const newGraph = await BackEndAPI.getCommitGraph();
      console.log(newGraph);
      props!.setCommits(newGraph.commits);
      props!.setBranchIDs(
        new Set(newGraph.commits.map((commit) => commit.branchId))
      );
      props!.setCurrentHeadID(newGraph.currentHead);
    } catch (error) {
      throw error;
    }
  }

  async function handleCheckout() {
    try {
      await BackEndAPI.rollbackBoth(props!.selectedCommitID!);
      const newGraph = await BackEndAPI.getCommitGraph();
      console.log(newGraph);
      props!.setCommits(newGraph.commits);
      props!.setBranchIDs(
        new Set(newGraph.commits.map((commit) => commit.branchId))
      );
      props!.setCurrentHeadID(newGraph.currentHead);
    } catch (error) {
      throw error;
    }
  }

  //*********************************************************************** */

  //**************Variables that are recreated per render*/
  //all the branches of GitGraph
  let branches = new Map<string, Branch>();
  let previousTag4SelectedCommit = props!.commits!.filter(
    (commit) => commit.oid === props!.selectedCommitID!
  )[0].tag;

  //initialize commits that are logically folded together into groups, reinitialize when commits are changed, or
  //visibility type is changed.
  useMemo(() => {
    console.log(
      "props.commit changed or judgeShow rule changed, re-calculate the groups again"
    );
    let newGroups = new Map<string, Commit[]>();
    let newGroupIndex = new Map<string, string>();
    let newIsGroupFolded = new Map<string, boolean>();
    let tmpBranchFolderHead = new Map<string, string>(); //remember current branch's folded group's head
    for (let element of props!.commits!) {
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
  }, [props!.commits, judgeShowFunctionID]);

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
          for (let element of props!.commits!) {
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
                  currentGroup![currentGroup!.length - 1].oid === element.oid
                ) {
                  addCommitToGraph(currentGroup![0], "➖");
                } else {
                }
              }
            }
          }
        }}
      </Gitgraph>

      {/****************************pop-ups ***********************/}
      {contextMenuPosition && (
        <ContextMenu
          setIsBranchNameEditorOpen={setIsBranchNameEditorOpen}
          x={contextMenuPosition.x}
          y={contextMenuPosition.y}
          onClose={handleCloseContextMenu}
          setIsTagEditorOpen={setIsTagEditorOpen}
          setJudgeFunctionID={setJudgeShowFunctionID}
          setIsGroupFolded={setIsGroupFolded}
          setIsWaitingModalOpen={setIsCheckoutWaitingModelOpen}
          setWaitingfor={setWaitingfor}
          judgeFunctionID={judgeShowFunctionID}
          isGroupFolded={isGroupFolded}
        />
      )}
      {mouseOverPosition && (
        <HoverPopup
          x={mouseOverPosition.x}
          y={mouseOverPosition.y}
          timestamp={mouseOverTimestamp}
        />
      )}
      <TagEditor
        isModalOpen={isTagEditorOpen}
        setIsModalOpen={setIsTagEditorOpen}
        defaultContent={
          previousTag4SelectedCommit ? previousTag4SelectedCommit : ""
        }
        submitHandler={handleTagSubmit}
        selectedHistoryID={props!.selectedCommitID!}
      ></TagEditor>
      <BranchNameEditor
        isModalOpen={isBranchNameEditorOpen}
        setIsModalOpen={setIsBranchNameEditorOpen}
        submitHandler={handleBranchNameSubmit}
        selectedHistoryID={props!.selectedCommitID!}
      ></BranchNameEditor>
      <CheckoutWaitingModal
        waitingFor={waitingFor}
        isWaitingModalOpen={isCheckoutWaitingModelOpen}
        setIsWaitingModalOpen={setIsCheckoutWaitingModelOpen}
        submitHandler={handleCheckout}
      ></CheckoutWaitingModal>
    </div>
  );
}

React.createElement("svg");
export default HistoryTree;
