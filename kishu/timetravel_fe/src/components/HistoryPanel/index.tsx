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
import { WaitingForModal } from "./WaitingForModal";

function HistoryTree() {
  const props = useContext(AppContext);
  console.log("rerender again");

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
  const [isWaitingModelOpen, setIsWaitingModelOpen] = useState(false);
  const [waitingFor, setWaitingfor] = useState(""); //wait for what, like tag, checkout or XXX
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
          onClick(commit) {
            props!.setSelectedCommitID(element.oid);
          },
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
  /************************************************************************** */

  //***********************event handelers************/
  function handleContextMenu(event: React.MouseEvent) {
    event.preventDefault();
    setContextMenuPosition({ x: event.clientX, y: event.clientY });
  }
  function handleCloseContextMenu() {
    setContextMenuPosition(null);
  }
  async function handleTagSubmit(newTag: string) {
    const data = await BackEndAPI.setTag(props!.selectedCommitID!!, newTag);
    // const data = await BackEndAPI.getInitialData();
    props!.setCommits(data!);
  }
  async function handleCheckout() {
    try {
      await BackEndAPI.rollbackBoth(props!.selectedCommitID!);
      const newCommits = await BackEndAPI.getInitialData();
      console.log(newCommits);
      props!.setCommits(newCommits!);
      props!.setBranchIDs(
        new Set(newCommits!.map((commit) => commit.branchId))
      );
    } catch (error) {
      setIsWaitingModelOpen(false);
      message.error("checkout error" + (error as Error).message);
    } finally {
      setIsWaitingModelOpen(false);
      message.info("checkout succeed");
    }
  }

  async function handleBranch(newBranchName: string) {
    try {
      await BackEndAPI.createBranch(newBranchName, props!.selectedCommitID!);
      const newCommits = await BackEndAPI.getInitialData();
      props!.setCommits(newCommits!);
      props!.setBranchIDs(
        new Set(newCommits!.map((commit) => commit.branchId))
      );
    } catch (error) {
      setIsWaitingModelOpen(false);
      message.error("create branch error" + (error as Error).message);
    } finally {
      setIsWaitingModelOpen(false);
      message.info("create branch succeed");
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
    console.log("calculating the groups again");
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
          x={contextMenuPosition.x}
          y={contextMenuPosition.y}
          onClose={handleCloseContextMenu}
          setIsTagEditorOpen={setIsTagEditorOpen}
          setJudgeFunctionID={setJudgeShowFunctionID}
          setIsGroupFolded={setIsGroupFolded}
          setIsWaitingModalOpen={setIsWaitingModelOpen}
          setWaitingfor={setWaitingfor}
          judgeFunctionID={judgeShowFunctionID}
          isGroupFolded={isGroupFolded}
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
      <WaitingForModal
        waitingFor={waitingFor}
        isWaitingModalOpen={isWaitingModelOpen}
        setIsWaitingModalOpen={setIsWaitingModelOpen}
        handleCheckout={handleCheckout}
        handelCreatebranch={handleBranch}
      ></WaitingForModal>
    </div>
  );
}

React.createElement("svg");
export default HistoryTree;
