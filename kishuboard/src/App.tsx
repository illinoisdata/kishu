import React, {
    createContext,
    useEffect,
    useMemo, useRef,
    useState,
} from "react";
import "./App.css";
import ReactSplit, {SplitDirection} from "@devbookhq/splitter";
import {Toolbar} from "./components/Toolbar";
import {HistoryPanel} from "./components/HistoryPanel";
import {NotebookFilePanel} from "./components/CodePanel/NotebookFilePanel";
import {BackEndAPI} from "./util/API";
import {Commit, CommitDetail} from "./util/Commit";
import {VariablePanel} from "./components/VariablePanel";
import {useParams} from "react-router-dom";
import {ExecutedCodePanel} from "./components/CodePanel/ExecutedCodePanel";
import {Tabs, TabsProps} from "antd";
import {NotebookFileDiffPanel} from "./components/CodePanel/NotebookFileDiffPanel";
import {ExecutedCodeDiffPanel} from "./components/CodePanel/ExecutedCodeDiffPanel";
import {DiffCodeDetail} from "./util/DiffCommitDetail";
import {logger} from "./log/logger";
import {OperationModals} from "./components/OperationModals";
import {DiffVarHunk} from "./util/DiffHunk";
import {VersionChange} from "./util/VariableVersionCompare";
import {Variable} from "./util/Variable";

function useInterval(callback: () => void, delay: number | null): void {
    const savedCallback = useRef<() => void>();

    // Remember the latest callback.
    useEffect(() => {
        savedCallback.current = callback;
    }, [callback]);

    // Set up the interval.
    useEffect(() => {
        function tick() {
            savedCallback.current!();
        }
        if (delay !== null) {
            let id = setInterval(tick, delay);
            return () => clearInterval(id);
        }
    }, [delay]);
}

interface appContextType {
    //control git graph
    commits: Commit[];
    setCommits: any;
    branchID2CommitMap: Map<string, string>;
    setBranchID2CommitMap: any;
    currentHeadID: string | undefined;
    setCurrentHeadID: any;
    currentHeadBranch: string | undefined;
    setCurrentHeadBranch: any;

    //control commit detail (non-diff)
    selectedCommit: CommitDetail | undefined;
    setSelectedCommit: any;
    selectedCommitID: string | undefined;
    setSelectedCommitID: any;
    selectedBranchID: string | undefined;
    setSelectedBranchID: any;

    //control diff. For diff, the origin commit id is selectedCommitID, the destination commit id is diffDestCommitID below
    // inDiffMode: boolean
    // setInDiffMode: any;
    diffCodeDetail: DiffCodeDetail | undefined;
    setDiffCodeDetail: any;
    diffVarDetail: DiffVarHunk[] | undefined;
    setDiffVarDetail: any;
    diffDestCommitID: string | undefined
    setDiffDestCommitID: any
}

interface operationModalContextType {
    //control modal render or not
    isTagEditorOpen: boolean;
    setIsTagEditorOpen: any;
    isMessageEditorOpen: boolean;
    setIsMessageEditorOpen: any;
    isBranchNameEditorOpen: boolean;
    setIsBranchNameEditorOpen: any;
    isCheckoutWaitingModalOpen: boolean;
    setIsCheckoutWaitingModalOpen: any;
    chooseCheckoutBranchModalOpen: boolean;
    setChooseCheckoutBranchModalOpen: any;

    //control modal content
    checkoutMode: string;
    setCheckoutMode: any;
    checkoutBranchID: string | undefined;
    setCheckoutBranchID: any;
    tagNameToBeEdit: string | undefined;
    setTagNameToBeEdit: any;
    branchNameToBeEdit: string | undefined;
    setBranchNameToBeEdit: any;
}

const cells_loading: TabsProps['items'] = [
    {
        key: '1',
        label: 'executed cells',
        children: 'No commit',
    },
    {
        key: '2',
        label: 'notebook cells',
        children: 'No commit',
    },
];

const cells: TabsProps['items'] = [
    {
        key: '1',
        label: 'executed cells',
        children: <div className="tile-xy notebook_panel executed_code_panel">
            {<ExecutedCodePanel/>}
        </div>,
    },
    {
        key: '2',
        label: 'notebook cells',
        children: <div className="tile-xy notebook_panel">
            {<NotebookFilePanel/>}
        </div>,
    },
];

const cells_diff: TabsProps['items'] = [
    {
        key: '1',
        label: 'executed cells',
        children: <div className="tile-xy notebook_panel executed_code_panel">
            {<ExecutedCodeDiffPanel/>}
        </div>,
    },
    {
        key: '2',
        label: 'notebook cells',
        children: <div className="tile-xy notebook_panel">
            {<NotebookFileDiffPanel/>}
        </div>,
    },
];

async function loadInitialData(setGlobalLoading: any, setError: any, setCommits: any, setBranchID2CommitMap: any, setSelectedCommitID: any, setSelectedBranchID: any, setCurrentHeadID: any, setCurrentHeadBranch: any) {
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
        setCurrentHeadBranch(data.currentHeadBranch);
        globalThis.NotebookName = await BackEndAPI.getNoteBookName(globalThis.NotebookID!);
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
        setSelectedCommit(data!);
    } catch (e) {
        if (e instanceof Error) {
            setError(e.message);
        }
    }
}

async function loadDiffCommitDetail(originCommitID: string, destinationCommitID: string, setDiffCodeDetail: any, setDiffVarDetail:any, setError: any) {
    try {
        const diffCodeDetail = await BackEndAPI.getCodeDiff(originCommitID, destinationCommitID);
        const variableCompares = await BackEndAPI.getDataDiff(originCommitID, destinationCommitID)
        const originCommitDetail = await BackEndAPI.getCommitDetail(originCommitID);
        const destinationCommitDetail = await BackEndAPI.getCommitDetail(destinationCommitID);
        //convert to maps
        let originVariableDetail:Map<string,Variable> = new Map<string, Variable>()
        originCommitDetail.variables.forEach((variableDetail)=>{
            originVariableDetail.set(variableDetail.variableName, variableDetail)
        })
        let destinationVariableDetail:Map<string,Variable> = new Map<string, Variable>()
        destinationCommitDetail.variables.forEach((variableDetail)=>{
            destinationVariableDetail.set(variableDetail.variableName, variableDetail)
        })
        const diffVarDetail: DiffVarHunk[] = []
        variableCompares.forEach((versionCompare)=>{
            if(versionCompare.option === "origin_only"){
                diffVarDetail.push({
                    option: 0,
                    content: originVariableDetail.get(versionCompare.variableName)!
                } as DiffVarHunk)
            }else if(versionCompare.option == "destination_only"){
                diffVarDetail.push({
                    option: VersionChange.destination_only,
                    content: destinationVariableDetail.get(versionCompare.variableName)!
                } as DiffVarHunk)
            }else if(versionCompare.option == "both_different_version"){
                diffVarDetail.push({
                    option: VersionChange.origin_only,
                    content: originVariableDetail.get(versionCompare.variableName)!,
                } as DiffVarHunk)
                diffVarDetail.push({
                    option: VersionChange.destination_only,
                    content: destinationVariableDetail.get(versionCompare.variableName)!,
                } as DiffVarHunk)
            }else if(versionCompare.option == "both_same_version"){
                diffVarDetail.push({
                    option: VersionChange.both_same_version,
                    content: originVariableDetail.get(versionCompare.variableName)!,
                } as DiffVarHunk)
            }
        })
        setDiffCodeDetail(diffCodeDetail!)
        setDiffVarDetail(diffVarDetail)
    } catch (e) {
        if (e instanceof Error) {
            setError(e.message);
            logger.error(e.message)
        }
    }
}

export const AppContext = createContext<appContextType | undefined>(undefined);
export const OperationModelContext = createContext<operationModalContextType | undefined>(undefined);

function App() {
    const [commits, setCommits] = useState<Commit[]>([]);
    const [selectedCommit, setSelectedCommit] = useState<CommitDetail>();
    const [diffCodeDetail, setDiffCodeDetail] = useState<DiffCodeDetail>();
    const [diffVarDetail, setDiffVarDetail] = useState<DiffVarHunk[]>([]);
    const [selectedCommitID, setSelectedCommitID] = useState<string>();
    const [selectedBranchID, setSelectedBranchID] = useState<string>();
    const [currentHeadID, setCurrentHeadID] = useState<string>();
    const [currentHeadBranch, setCurrentHeadBranch] = useState<string>();
    const [branchID2CommitMap, setBranchID2CommitMap] = useState<
        Map<string, string>
    >(new Map());
    // const [inDiffMode, setInDiffMode] = useState<boolean>(false);
    const [diffDestCommitID, setDiffDestCommitID] = useState<string | undefined>(undefined)
    const [searchResultIds, setSearchResultIds] = useState<string[]>([]);

    //********status of pop-ups************************ */
    const [isTagEditorOpen, setIsTagEditorOpen] = useState(false);
    const [isMessageEditorOpen, setIsMessageEditorOpen] = useState(false);
    const [isBranchNameEditorOpen, setIsBranchNameEditorOpen] = useState(false);
    const [isCheckoutWaitingModalOpen, setIsCheckoutWaitingModalOpen] =
        useState(false);
    const [chooseCheckoutBranchModalOpen, setChooseCheckoutBranchModalOpen] =
        useState(false);
    const [checkoutMode, setCheckoutMode] = useState(""); //wait for what, like tag, checkout or XXX
    const [checkoutBranchID, setCheckoutBranchID] = useState<string | undefined>(
        undefined,
    );
    const [tagNameToBeEdit, setTagNameToBeEdit] = useState<string | undefined>(undefined);
    const [branchNameToBeEdit, setBranchNameToBeEdit] = useState<string | undefined>(
        undefined,
    );

    const appContext: appContextType = {
        commits,
        setCommits,
        branchID2CommitMap,
        setBranchID2CommitMap,
        currentHeadID,
        setCurrentHeadID,
        currentHeadBranch,
        setCurrentHeadBranch,

        selectedCommit,
        setSelectedCommit,
        selectedCommitID,
        setSelectedCommitID,
        selectedBranchID,
        setSelectedBranchID,

        // inDiffMode,
        // setInDiffMode,
        diffCodeDetail,
        setDiffCodeDetail,
        diffVarDetail,
        setDiffVarDetail,
        diffDestCommitID,
        setDiffDestCommitID
    };

    const operationModelContext: operationModalContextType = {
        isTagEditorOpen,
        setIsTagEditorOpen,
        isMessageEditorOpen,
        setIsMessageEditorOpen,
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
        tagNameToBeEdit,
        setTagNameToBeEdit,
        branchNameToBeEdit,
        setBranchNameToBeEdit,
    }

    const [globalLoading, setGlobalLoading] = useState(true);
    const [error, setError] = useState<string | undefined>(undefined);

    const [splitSizes1, setSplitSizes1] = useState([30, 70]);
    const [splitSizes2, setSplitSizes2] = useState([60, 40]);

    //whether or not to scroll history panel to searched result
    const [scrollToResult, setScrollToResult] = useState(false);
    const scrollableHisPanel = useRef<HTMLDivElement>(null);

    globalThis.NotebookID = useParams().notebookName;

    useEffect(() => {
        //initialize the states
        loadInitialData(setGlobalLoading, setError, setCommits, setBranchID2CommitMap, setSelectedCommitID, setSelectedBranchID, setCurrentHeadID, setCurrentHeadBranch);
    }, []);

    useInterval(() => {
        // Your custom logic here
        refreshGraph();
    }, 1000);

    // useMemo(() => {
    //     loadCommitDetail(selectedCommitID!, setSelectedCommit, setError);
    //     if (inDiffMode && currentHeadID) {
    //         loadDiffCommitDetail(selectedCommitID!, diffDestCommitID?diffDestCommitID:currentHeadID!, setDiffCodeDetail, setDiffVarDetail, setError)
    //     }
    // }, [selectedCommitID, currentHeadID, inDiffMode, diffDestCommitID]);

    useMemo(() => {
        loadCommitDetail(selectedCommitID!, setSelectedCommit, setError);
        if (diffDestCommitID && currentHeadID) {
            loadDiffCommitDetail(selectedCommitID!, diffDestCommitID?diffDestCommitID:currentHeadID!, setDiffCodeDetail, setDiffVarDetail, setError)
        }
    }, [selectedCommitID, currentHeadID, diffDestCommitID]);

    async function refreshGraph(){
        const newGraph = await BackEndAPI.getCommitGraph();
        //do a deap comparison of the commits
        if(JSON.stringify(newGraph.commits) !== JSON.stringify(commits)){
        setCommits(newGraph.commits);
        const newSetBranchID2CommitMap = new Map<string, string>();
        commits.forEach((commit) => {
            commit.branchIds.forEach((branchID) => {
                newSetBranchID2CommitMap.set(branchID, commit.oid);
            });
        });
        setBranchID2CommitMap(newSetBranchID2CommitMap);
        setCurrentHeadBranch(newGraph.currentHeadBranch)
        setCurrentHeadID(newGraph.currentHead);
        if(!selectedCommitID) {
            setSelectedCommitID(newGraph.currentHead);
            setSelectedBranchID(newGraph.currentHeadBranch);
        }
        await refreshSelectedCommit();}
    }

    async function refreshSelectedCommit(){
        await loadCommitDetail(selectedCommitID!, setSelectedCommit, setError);
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
                        {/*<Toolbar setInDiffMode={setInDiffMode} setSearchResultIds={setSearchResultIds}/>*/}
                        <Toolbar setSearchResultIds={setSearchResultIds} setScrollToHighlightSignal={setScrollToResult} currentSignal={scrollToResult}/>
                        <ReactSplit
                            direction={SplitDirection.Horizontal}
                            initialSizes={splitSizes1}
                            onResizeFinished={(pairInd, newSizes) => {
                                setSplitSizes1(newSizes);
                            }}
                            gutterClassName="custom_gutter"

                        >
                            <div className="tile-xy history_panel">
                                {/*<HistoryPanel highlighted_commit_ids={searchResultIds} refreshGraphHandler={refreshGraph} width={splitSizes1[0]} scrollSignal={scrollToResult} scrollableHisPanel={scrollableHisPanel}/>*/}
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
                                        <p>No commit</p>
                                    </div>
                                </div>
                            </ReactSplit>
                        </ReactSplit>
                    </>
                )}

                {!globalLoading && !error && selectedCommit && (
                    <>
                        {/*<Toolbar setInDiffMode={setInDiffMode} setSearchResultIds={setSearchResultIds}/>*/}
                        <Toolbar setSearchResultIds={setSearchResultIds} setScrollToHighlightSignal={setScrollToResult} currentSignal={scrollToResult}/>
                        <ReactSplit
                            direction={SplitDirection.Horizontal}
                            initialSizes={splitSizes1}
                            onResizeFinished={(pairInd, newSizes) => {
                                setSplitSizes1(newSizes);
                            }}
                            gutterClassName="custom_gutter"
                        >
                            <OperationModelContext.Provider value={operationModelContext}>
                                <div className="tile-xy  history_panel" ref={scrollableHisPanel}>
                                    <HistoryPanel highlighted_commit_ids={searchResultIds} refreshGraphHandler={refreshGraph} width={splitSizes1[0]} scrollSignal={scrollToResult} scrollableHisPanel={scrollableHisPanel}/>
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
                                    {diffDestCommitID ? <Tabs defaultActiveKey="1" items={cells_diff} tabBarStyle={{marginBottom:0, paddingLeft:40}}/> :
                                        <Tabs defaultActiveKey="1" items={cells} tabBarStyle={{marginBottom:0, paddingLeft:40}}/>}
                                </div>
                                <div className="tile-xy">
                                    <VariablePanel variables={diffDestCommitID?diffVarDetail!:selectedCommit!.variables!} diffMode={!!diffDestCommitID}/>
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
