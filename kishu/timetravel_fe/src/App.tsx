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
import { Commit } from "./util/Commit";
import VariablePanel from "./components/VariablePanel";
import { useParams } from "react-router-dom";

interface appContextType {
  commits: Commit[];
  setCommits: any;
  branchIDs: Set<String> | undefined;
  setBranchIDs: any;
  selectedCommit: Commit | undefined;
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
  const [branchIDs, setBranchIDs] = useState<Set<String>>();
  const [selectedCommit, setSelectedCommit] = useState<Commit>();
  const [selectedCommitID, setSelectedCommitID] = useState<string>();
  const [selectedBranchID, setSelectedBranchID] = useState<string>();
  const [currentHeadID, setCurrentHeadID] = useState<string>();
  const appContext: appContextType = {
    commits,
    setCommits,
    branchIDs,
    setBranchIDs,
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

  globalThis.NotebookID = useParams().notebookName;

  useEffect(() => {
    //initialize the states
    async function loadInitialData() {
      console.log("load initial data now!");
      setGlobalLoading(true);
      try {
        const data = await BackEndAPI.getCommitGraph();
        console.log(data);
        setCommits(data.commits);
        setBranchIDs(new Set(data.commits.map((commit) => commit.branchId)));
        setSelectedCommitID(data.currentHead);
        setSelectedBranchID(data.currentHeadBranch);
        setCurrentHeadID(data.currentHead);
      } catch (e) {
        if (e instanceof Error) {
          setError(e.message);
        }
      } finally {
        console.log("initial data is loaded now!");
        setGlobalLoading(false);
      }
    }
    loadInitialData();
  }, []);

  useMemo(() => {
    async function loadCommitDetail(selectedCommitID: string) {
      console.log("useMemo to load detail of commit " + selectedCommitID);
      if (!selectedCommitID) {
        return;
      }
      try {
        const data = await BackEndAPI.getCommitDetail(selectedCommitID);
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
                <div className="tile-xy u-showbottom" ref={codePanelRef}>
                  {<CodePanel containerRef={codePanelRef} />}
                </div>
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
