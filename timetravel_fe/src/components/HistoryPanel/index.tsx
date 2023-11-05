/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 13:46:16
 * @LastEditTime: 2023-08-01 13:21:53
 * @FilePath: /src/components/HistoryPanel/ExecutedCodePanel.tsx
 * @Description:
 */
import {Commit} from "../../util/Commit";
import React, {
    useContext,
    useMemo,
    useState,
} from "react";
import ContextMenu from "./ContextMenu";
import TagEditor from "./TagEditor";
import {BackEndAPI} from "../../util/API";
import {AppContext} from "../../App";
import {CheckoutWaitingModal} from "./CheckoutWaitingForModal";
import BranchNameEditor from "./BranchNameEditor";
import {HistoryGraph} from "./HistoryGraph";
import {getPointRenderInfos} from "../../util/getPointRenderInfo";
import "./historyPanel.css";
import {CommitInfo} from "./CommitInfo";
import {PointRenderInfo} from "../../util/PointRenderInfo";
import {CheckoutBranchModel} from "./CheckoutBranchModel";
import logger from "../../log/logger";

function HistoryTree() {
    const props = useContext(AppContext);

    //***********************state for git graph************************ */
    const [pointRenderInfos, setPointRenderInfos] = useState<
        Map<string, PointRenderInfo>
    >(new Map());
    const [svgMaxX, setsvgMaxX] = useState<number>(0);
    const [svgMaxY, setsvgMaxY] = useState<number>(0);

    //********status of pop-ups************************ */
    const [contextMenuPosition, setContextMenuPosition] = useState<{
        x: number;
        y: number;
    } | null>(null);
    const [isTagEditorOpen, setIsTagEditorOpen] = useState(false);
    const [isBranchNameEditorOpen, setIsBranchNameEditorOpen] = useState(false);
    const [isCheckoutWaitingModelOpen, setIsCheckoutWaitingModelOpen] =
        useState(false);
    const [chooseCheckoutBranchModelOpen, setChooseCheckoutBranchModelOpen] =
        useState(false);
    const [checkoutMode, setCheckoutMode] = useState(""); //wait for what, like tag, checkout or XXX
    const [checkoutBranchID, setCheckoutBranchID] = useState<string | undefined>(
        undefined,
    );

//********************************************************************* */

    /************************************************************************** */

    //***********************event handelers************/
    function handleCloseContextMenu() {
        setContextMenuPosition(null);
    }

    async function handleTagSubmit(newTag: string) {
        try {
            await BackEndAPI.setTag(props!.selectedCommitID!!, newTag);
            const newGraph = await BackEndAPI.getCommitGraph();
            logger.silly("tag submit, git graph after parse:", newGraph);
            props!.setCommits(newGraph.commits);
            const newSetBranchID2CommitMap = new Map<string, string>();
            props!.commits.forEach((commit) => {
                commit.branchIds.forEach((branchID) => {
                    newSetBranchID2CommitMap.set(branchID, commit.oid);
                });
            });
            props!.setBranchID2CommitMap(newSetBranchID2CommitMap);
            props!.setCurrentHeadID(newGraph.currentHead);
        } catch (error) {
            throw error;
        }
    }

    async function handleBranchNameSubmit(newBranchName: string) {
        try {
            await BackEndAPI.createBranch(props!.selectedCommitID!, newBranchName);
            const newGraph = await BackEndAPI.getCommitGraph();
            logger.silly("branch name submit, git graph after parse:", newGraph);
            props!.setCommits(newGraph.commits);
            const newSetBranchID2CommitMap = new Map<string, string>();
            props!.commits.forEach((commit) => {
                commit.branchIds.forEach((branchID) => {
                    newSetBranchID2CommitMap.set(branchID, commit.oid);
                });
            });
            props!.setBranchID2CommitMap(newSetBranchID2CommitMap);
            props!.setCurrentHeadID(newGraph.currentHead);
        } catch (error) {
            throw error;
        }
    }

    async function handleCheckoutBoth(branchID?: string) {
        try {
            await BackEndAPI.rollbackBoth(props!.selectedCommitID!, branchID);
            const newGraph = await BackEndAPI.getCommitGraph();
            logger.silly("checkout submit, git graph after parse:", newGraph);
            props!.setCommits(newGraph.commits);
            const newSetBranchID2CommitMap = new Map<string, string>();
            props!.commits.forEach((commit) => {
                commit.branchIds.forEach((branchID) => {
                    newSetBranchID2CommitMap.set(branchID, commit.oid);
                });
            });
            props!.setBranchID2CommitMap(newSetBranchID2CommitMap);
            props!.setCurrentHeadID(newGraph.currentHead);
        } catch (error) {
            throw error;
        }
    }

    async function handleCheckoutVariable(branchID?: string) {
        try {
            await BackEndAPI.rollbackVariables(props!.selectedCommitID!, branchID);
            const newGraph = await BackEndAPI.getCommitGraph();
            logger.silly("checkout submit, git graph after parse:", newGraph);
            props!.setCommits(newGraph.commits);
            const newSetBranchID2CommitMap = new Map<string, string>();
            props!.commits.forEach((commit) => {
                commit.branchIds.forEach((branchID) => {
                    newSetBranchID2CommitMap.set(branchID, commit.oid);
                });
            });
            props!.setBranchID2CommitMap(newSetBranchID2CommitMap);
            props!.setCurrentHeadID(newGraph.currentHead);
        } catch (error) {
            throw error;
        }
    }

    //*********************************************************************** */

    let commitIDMap = new Map<string, Commit>();
    props?.commits.map((commit) => commitIDMap.set(commit.oid, commit));

    //usememo for pointRenderInfos
    useMemo(() => {
        let infos = getPointRenderInfos(props?.commits!);
        setPointRenderInfos(infos["info"]);
        setsvgMaxX(infos["maxX"]);
        setsvgMaxY(infos["maxY"]);
    }, [props?.commits]);

    const commitInfos = props?.commits.map((commit) => {
        return (
            <CommitInfo
                commit={commit}
                pointRendererInfo={pointRenderInfos.get(commit.oid)!}
                onclick={() => {
                    props!.setSelectedCommitID(commit.oid);
                    props!.setSelectedBranchID("");
                }}
                onContextMenu={(event: React.MouseEvent) => {
                    event.preventDefault();
                    props!.setSelectedCommitID(commit.oid);
                    props!.setSelectedBranchID("");
                    setContextMenuPosition({x: event.clientX, y: event.clientY});
                }}
            />
        );
    });

    return (
        <div className="historyPanel" onClick={handleCloseContextMenu}>
            <HistoryGraph
                Commits={commitIDMap}
                pointRendererInfos={pointRenderInfos}
                selectedCommitID={props?.selectedCommitID!}
                currentCommitID={props?.currentHeadID!}
                svgMaxX={svgMaxX}
                svgMaxY={svgMaxY}
            />
            <div className={"commitInfos"}>{commitInfos}</div>
            {/****************************pop-ups ***********************/}
            {contextMenuPosition && (
                <ContextMenu
                    setIsBranchNameEditorOpen={setIsBranchNameEditorOpen}
                    x={contextMenuPosition.x}
                    y={contextMenuPosition.y}
                    onClose={handleCloseContextMenu}
                    setIsTagEditorOpen={setIsTagEditorOpen}
                    setIsCheckoutWaitingModalOpen={setIsCheckoutWaitingModelOpen}
                    setChckoutMode={setCheckoutMode}
                    setChooseCheckoutBranchModelOpen={setChooseCheckoutBranchModelOpen}
                />
            )}
            <TagEditor
                isModalOpen={isTagEditorOpen}
                setIsModalOpen={setIsTagEditorOpen}
                submitHandler={handleTagSubmit}
                selectedHistoryID={props!.selectedCommitID!}
            ></TagEditor>
            <BranchNameEditor
                isModalOpen={isBranchNameEditorOpen}
                setIsModalOpen={setIsBranchNameEditorOpen}
                submitHandler={handleBranchNameSubmit}
                selectedHistoryID={props!.selectedCommitID!}
            ></BranchNameEditor>
            <CheckoutBranchModel
                branchIDOptions={props?.selectedCommit?.commit.branchIds}
                isModalOpen={chooseCheckoutBranchModelOpen}
                setCheckoutBranchID={setCheckoutBranchID}
                setIsCheckoutWaitingModalOpen={setIsCheckoutWaitingModelOpen}
                setIsModalOpen={setChooseCheckoutBranchModelOpen}
            ></CheckoutBranchModel>
            <CheckoutWaitingModal
                checkoutMode={checkoutMode}
                isWaitingModalOpen={isCheckoutWaitingModelOpen}
                setIsWaitingModalOpen={setIsCheckoutWaitingModelOpen}
                checkoutBothHandler={handleCheckoutBoth}
                checkoutVariableHandler={handleCheckoutVariable}
                checkoutBranchID={checkoutBranchID}
                setCheckoutBranchID={setCheckoutBranchID} //after checkout succeed, the checkoutBranchID will be set to undefined
            ></CheckoutWaitingModal>
        </div>
    );
}

React.createElement("svg");
export default HistoryTree;