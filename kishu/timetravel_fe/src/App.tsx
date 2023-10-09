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
  useRef,
  useState,
} from "react";
import "./App.css";
import ReactSplit, { SplitDirection } from "@devbookhq/splitter";
import Toolbar from "./components/Toolbar";
import HistoryTree from "./components/HistoryPanel";
import CodePanel from "./components/CodePanel";
import { BackEndAPI } from "./util/API";
import { Commit, CommitDetail } from "./util/Commit";
import VariablePanel from "./components/VariablePanel";
import { useParams } from "react-router-dom";
import ExecutedCodePanel from "./components/CodePanel/ExecutedCodePanel";

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
}

export const AppContext = createContext<appContextType | undefined>(undefined);

function App() {
  const [commits, setCommits] = useState<Commit[]>([]);
  const [selectedCommit, setSelectedCommit] = useState<CommitDetail>();
  const [selectedCommitID, setSelectedCommitID] = useState<string>();
  const [selectedBranchID, setSelectedBranchID] = useState<string>();
  const [currentHeadID, setCurrentHeadID] = useState<string>();
  const [branchID2CommitMap, setBranchID2CommitMap] = useState<
    Map<string, string>
  >(new Map());
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
  };

  const [globalLoading, setGlobalLoading] = useState(true);
  const [error, setError] = useState<string | undefined>(undefined);

  const [splitSizes1, setSplitSizes1] = useState([20, 80]);
  const [splitSizes2, setSplitSizes2] = useState([53, 47]);
  const [splitSizes3, setSplitSizes3] = useState([50, 50]);

  globalThis.NotebookID = useParams().notebookName;

  useEffect(() => {
    //initialize the states
    async function loadInitialData() {
      setGlobalLoading(true);
      try {
        const data = await BackEndAPI.getCommitGraph();
        console.log("git graph after parse:");
        console.log(data);
        setCommits(data.commits);
        const newSetBranchID2CommitMap = new Map<string, string>();
        data.commits.map((commit) => {
          commit.branchIds.map((branchID) => {
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

    loadInitialData();
  }, []);

  useMemo(() => {
    async function loadCommitDetail(selectedCommitID: string) {
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

    loadCommitDetail(selectedCommitID!);
  }, [selectedCommitID]);

  let codePanelRef = useRef<HTMLDivElement | null>(null);
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
            <Toolbar />
            <ReactSplit
              direction={SplitDirection.Horizontal}
              initialSizes={splitSizes1}
              onResizeFinished={(pairInd, newSizes) => {
                setSplitSizes1(newSizes);
              }}
              gutterClassName="custom_gutter"
            >
              <div className="tile-xy">
                <HistoryTree />
              </div>
              <ReactSplit
                direction={SplitDirection.Vertical}
                initialSizes={splitSizes2}
                onResizeFinished={(pairInd, newSizes) => {
                  setSplitSizes2(newSizes);
                }}
                gutterClassName="custom_gutter"
              >
                <div className="tile-xy u-showbottom">
                  <div className="center-page">
                    <p>Loading...</p>
                  </div>
                </div>
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
            <Toolbar />
            <ReactSplit
              direction={SplitDirection.Horizontal}
              initialSizes={splitSizes1}
              onResizeFinished={(pairInd, newSizes) => {
                setSplitSizes1(newSizes);
              }}
              gutterClassName="custom_gutter"
            >
              <div className="tile-xy">
                <HistoryTree />
              </div>
              <ReactSplit
                direction={SplitDirection.Vertical}
                initialSizes={splitSizes2}
                onResizeFinished={(pairInd, newSizes) => {
                  setSplitSizes2(newSizes);
                }}
                gutterClassName="custom_gutter"
              >
                <ReactSplit
                  direction={SplitDirection.Horizontal}
                  initialSizes={splitSizes3}
                  onResizeFinished={(pairInd, newSizes) => {
                    setSplitSizes3(newSizes);
                  }}
                  gutterClassName="custom_gutter"
                >
                  <div className="tile-xy u-showbottom">
                    {<ExecutedCodePanel />}
                  </div>
                  <div className="tile-xy u-showbottom" ref={codePanelRef}>
                    {<CodePanel containerRef={codePanelRef} />}
                  </div>
                </ReactSplit>
                <div className="tile-xy">
                  <VariablePanel variables={selectedCommit!.variables!} />
                </div>
              </ReactSplit>
            </ReactSplit>
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
