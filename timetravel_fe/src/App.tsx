/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 10:34:27
 * @LastEditTime: 2023-08-01 10:51:15
 * @FilePath: /src/App.tsx
 * @Description:
 */
import React, {
    createContext,
    useEffect,
    useMemo,
    useState,
} from "react";
import "./App.css";
import ReactSplit, {SplitDirection} from "@devbookhq/splitter";
import {Toolbar} from "./components/Toolbar";
import HistoryPanel from "./components/HistoryPanel";
import NotebookFilePanel from "./components/CodePanel/NotebookFilePanel";
import {BackEndAPI} from "./util/API";
import {Commit, CommitDetail} from "./util/Commit";
import VariablePanel from "./components/VariablePanel";
import {useParams} from "react-router-dom";
import ExecutedCodePanel from "./components/CodePanel/ExecutedCodePanel";
import {Tabs, TabsProps} from "antd";
import NotebookFileDiffPanel from "./components/CodePanel/NotebookFileDiffPanel";
import ExecutedCodeDiffPanel from "./components/CodePanel/ExecutedCodeDiffPanel";
import {DiffCommitDetail} from "./util/DiffCommitDetail";
import logger from "./log/logger";
import OperationModals from "./components/OperationModals";

interface appContextType {
    commits: Commit[];
    setCommits: any;
    branchID2CommitMap: Map<string, string>;
    setBranchID2CommitMap: any;
    selectedCommit: CommitDetail | undefined;
    setSelectedCommit: any;
    selectedCommitID: string | undefined;
    setSelectedCommitID: any;
    selectedBranchID: string | undefined;
    setSelectedBranchID: any;
    currentHeadID: string | undefined;
    setCurrentHeadID: any;
    inDiffMode: boolean
    setInDiffMode: any;
    DiffCommitDetail: DiffCommitDetail | undefined;
    setDiffCommitDetail: any;
    diffDestCommitID: string | undefined
    setDiffDestCommitID: any
}

interface operationModalContextType {
    //control model render or not
    isTagEditorOpen: boolean;
    setIsTagEditorOpen: any;
    isBranchNameEditorOpen: boolean;
    setIsBranchNameEditorOpen: any;
    isCheckoutWaitingModalOpen: boolean;
    setIsCheckoutWaitingModalOpen: any;
    chooseCheckoutBranchModalOpen: boolean;
    setChooseCheckoutBranchModalOpen: any;

    //control model content
    checkoutMode: string;
    setCheckoutMode: any;
    checkoutBranchID: string | undefined;
    setCheckoutBranchID: any;
}

const cells_loading: TabsProps['items'] = [
    {
        key: '1',
        label: 'notebook cells',
        children: 'loading...',
    },
    {
        key: '2',
        label: 'executed cells',
        children: 'loading...',
    }
];

const cells: TabsProps['items'] = [
    {
        key: '1',
        label: 'notebook cells',
        children: <div className="tile-xy notebook_panel">
            {<NotebookFilePanel/>}
        </div>,
    },
    {
        key: '2',
        label: 'executed cells',
        children: <div className="tile-xy notebook_panel">
            {<ExecutedCodePanel/>}
        </div>,
    }
];

const cells_diff: TabsProps['items'] = [
    {
        key: '1',
        label: 'notebook cells',
        children: <div className="tile-xy notebook_panel">
            {<NotebookFileDiffPanel/>}
        </div>,
    },
    {
        key: '2',
        label: 'executed cells',
        children: <div className="tile-xy notebook_panel">
            {<ExecutedCodeDiffPanel/>}
        </div>,
    }
];

async function loadInitialData(setGlobalLoading: any, setError: any, setCommits: any, setBranchID2CommitMap: any, setSelectedCommitID: any, setSelectedBranchID: any, setCurrentHeadID: any) {
    setGlobalLoading(true);
    try {
        const data = await BackEndAPI.getCommitGraph();
        logger.silly("git graph after parse:", data);
        setCommits(data.commits);
        const newSetBranchID2CommitMap = new Map<string, string>();
        data.commits.forEach((commit) => {
            commit.branchIds.forEach((branchID) => {
                newSetBranchID2CommitMap.set(branchID, commit.oid);
            });
        });
        setBranchID2CommitMap(newSetBranchID2CommitMap);
        setSelectedCommitID(data.currentHead);
        setSelectedBranchID(data.currentHeadBranch);
        setCurrentHeadID(data.currentHead);
    } catch (e) {
        if (e instanceof Error) {
            setError(e.message);
        }
    } finally {
        setGlobalLoading(false);
    }
}

async function loadCommitDetail(selectedCommitID: string, setSelectedCommit: any, setError: any) {
    if (!selectedCommitID) {
        return;
    }
    try {
        const data = await BackEndAPI.getCommitDetail(selectedCommitID);
        console.log("commit detail after parse:");
        console.log(data);
        setSelectedCommit(data!);
    } catch (e) {
        if (e instanceof Error) {
            setError(e.message);
        }
    }
}

async function loadDiffCommitDetail(selectedCommitID: string, currentHeadID: string | undefined, setDiffCommitDetail: any, setError: any) {
    if (!selectedCommitID) {
        return;
    }
    try {
        const data = await BackEndAPI.getDiff(selectedCommitID, currentHeadID!);
        console.log("commit detail diff after parse:");
        console.log(data);
        setDiffCommitDetail(data!)
    } catch (e) {
        if (e instanceof Error) {
            setError(e.message);
        }
    }
}

export const AppContext = createContext<appContextType | undefined>(undefined);
export const OperationModelContext = createContext<operationModalContextType | undefined>(undefined);

function App() {
    const [commits, setCommits] = useState<Commit[]>([]);
    const [selectedCommit, setSelectedCommit] = useState<CommitDetail>();
    const [DiffCommitDetail, setDiffCommitDetail] = useState<DiffCommitDetail>();
    const [selectedCommitID, setSelectedCommitID] = useState<string>();
    const [selectedBranchID, setSelectedBranchID] = useState<string>();
    const [currentHeadID, setCurrentHeadID] = useState<string>();
    const [branchID2CommitMap, setBranchID2CommitMap] = useState<
        Map<string, string>
    >(new Map());
    const [inDiffMode, setInDiffMode] = useState<boolean>(false);
    const [highlighted_commit_ids, setHighlighted_commit_ids] = useState<string[]>([]);
    //for diff
    const [diffDestCommitID, setDiffDestCommitID] = useState<string | undefined>(undefined)

    //********status of pop-ups************************ */
    const [isTagEditorOpen, setIsTagEditorOpen] = useState(false);
    const [isBranchNameEditorOpen, setIsBranchNameEditorOpen] = useState(false);
    const [isCheckoutWaitingModalOpen, setIsCheckoutWaitingModalOpen] =
        useState(false);
    const [chooseCheckoutBranchModalOpen, setChooseCheckoutBranchModalOpen] =
        useState(false);
    const [checkoutMode, setCheckoutMode] = useState(""); //wait for what, like tag, checkout or XXX
    const [checkoutBranchID, setCheckoutBranchID] = useState<string | undefined>(
        undefined,
    );

    const appContext: appContextType = {
        commits,
        setCommits,
        branchID2CommitMap,
        setBranchID2CommitMap,
        selectedCommit,
        setSelectedCommit,
        selectedCommitID,
        setSelectedCommitID,
        selectedBranchID,
        setSelectedBranchID,
        currentHeadID,
        setCurrentHeadID,
        inDiffMode,
        setInDiffMode,
        DiffCommitDetail,
        setDiffCommitDetail,
        diffDestCommitID,
        setDiffDestCommitID
    };

    const operationModelContext: operationModalContextType = {
        isTagEditorOpen,
        setIsTagEditorOpen,
        isBranchNameEditorOpen,
        setIsBranchNameEditorOpen,
        isCheckoutWaitingModalOpen,
        setIsCheckoutWaitingModalOpen,
        chooseCheckoutBranchModalOpen,
        setChooseCheckoutBranchModalOpen,
        checkoutMode,
        setCheckoutMode,
        checkoutBranchID,
        setCheckoutBranchID,
    }

    const [globalLoading, setGlobalLoading] = useState(true);
    const [error, setError] = useState<string | undefined>(undefined);

    const [splitSizes1, setSplitSizes1] = useState([30, 70]);
    const [splitSizes2, setSplitSizes2] = useState([60, 40]);

    globalThis.NotebookID = useParams().notebookName;

    useEffect(() => {
        //initialize the states
        loadInitialData(setGlobalLoading, setError, setCommits, setBranchID2CommitMap, setSelectedCommitID, setSelectedBranchID, setCurrentHeadID);
    }, []);

    useMemo(() => {
        loadCommitDetail(selectedCommitID!, setSelectedCommit, setError);
        if (inDiffMode && currentHeadID) {
            loadDiffCommitDetail(selectedCommitID!, currentHeadID, setDiffCommitDetail, setError)
        }
    }, [selectedCommitID, currentHeadID, inDiffMode]);

    useMemo(() => {
        if (inDiffMode) {
            loadDiffCommitDetail(selectedCommitID!, currentHeadID, setDiffCommitDetail, setError)
        }
    }, [inDiffMode, currentHeadID, selectedCommitID]);

    async function refreshGraph(){
        const newGraph = await BackEndAPI.getCommitGraph();
        logger.silly("checkout submit, git graph after parse:", newGraph);
        setCommits(newGraph.commits);
        const newSetBranchID2CommitMap = new Map<string, string>();
        commits.forEach((commit) => {
            commit.branchIds.forEach((branchID) => {
                newSetBranchID2CommitMap.set(branchID, commit.oid);
            });
        });
        setBranchID2CommitMap(newSetBranchID2CommitMap);
        setCurrentHeadID(newGraph.currentHead);
    }


    return (
        <AppContext.Provider value={appContext}>
            <>
                {error && (
                    <>
                        <div className="center-page">
                            <p>{error}</p>
                        </div>
                    </>
                )}

                {/* only the history tree has been loaded */}
                {!globalLoading && !error && !selectedCommit && (
                    <>
                        <Toolbar setInDiffMode={setInDiffMode} setHighightedCommitIds={setHighlighted_commit_ids}/>
                        <ReactSplit
                            direction={SplitDirection.Horizontal}
                            initialSizes={splitSizes1}
                            onResizeFinished={(pairInd, newSizes) => {
                                setSplitSizes1(newSizes);
                            }}
                            gutterClassName="custom_gutter"

                        >
                            <div className="tile-xy history_panel">
                                <HistoryPanel highlighted_commit_ids={highlighted_commit_ids}/>
                            </div>

                            <ReactSplit
                                direction={SplitDirection.Vertical}
                                initialSizes={splitSizes2}
                                onResizeFinished={(pairInd, newSizes) => {
                                    setSplitSizes2(newSizes);
                                }}
                                gutterClassName="custom_gutter"
                            >
                                <Tabs defaultActiveKey="1" items={cells_loading}/>
                                <div className="tile-xy">
                                    <div className="center-page">
                                        <p>Loading...</p>
                                    </div>
                                </div>
                            </ReactSplit>
                        </ReactSplit>
                    </>
                )}

                {!globalLoading && !error && selectedCommit && (
                    <>
                        <Toolbar setInDiffMode={setInDiffMode} setHighightedCommitIds={setHighlighted_commit_ids}/>
                        <ReactSplit
                            direction={SplitDirection.Horizontal}
                            initialSizes={splitSizes1}
                            onResizeFinished={(pairInd, newSizes) => {
                                setSplitSizes1(newSizes);
                            }}
                            gutterClassName="custom_gutter"
                        >
                            <OperationModelContext.Provider value={operationModelContext}>
                                <div className="tile-xy  history_panel">
                                    <HistoryPanel highlighted_commit_ids={highlighted_commit_ids}/>
                                </div>
                            </OperationModelContext.Provider>
                            <ReactSplit
                                direction={SplitDirection.Vertical}
                                initialSizes={splitSizes2}
                                onResizeFinished={(pairInd, newSizes) => {
                                    setSplitSizes2(newSizes);
                                }}
                                gutterClassName="custom_gutter"
                            >
                                <div className="tile-xy u-showbottom">
                                    {inDiffMode ? <Tabs defaultActiveKey="1" items={cells_diff}/> :
                                        <Tabs defaultActiveKey="1" items={cells}/>}
                                </div>
                                <div className="tile-xy">
                                    <VariablePanel variables={selectedCommit!.variables!}/>
                                </div>
                            </ReactSplit>
                        </ReactSplit>
                        <OperationModelContext.Provider value={operationModelContext}>
                            <OperationModals selectedCommitID={selectedCommitID!} refreshGraphHandler={refreshGraph} selectedCommit={selectedCommit!}/>
                        </OperationModelContext.Provider>
                    </>
                )}

                {globalLoading && (
                    <div className="center-page">
                        <p>Loading...</p>
                    </div>
                )}
            </>
        </AppContext.Provider>
    );
}

export default App;
