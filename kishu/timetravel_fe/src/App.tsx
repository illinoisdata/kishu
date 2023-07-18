/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 10:34:27
 * @LastEditTime: 2023-07-18 14:53:12
 * @FilePath: /src/App.tsx
 * @Description:
 */
import React, { useEffect, useState } from "react";
import "./App.css";
import ReactSplit, { SplitDirection } from "@devbookhq/splitter";
// import { useEffect, useState } from "react";
import Toolbar from "./components/Toolbar";
import HistoryTree from "./components/HistoryPanel/HistoryTree";
import SearchPanel from "./components/SearchPanel";
import CodePanel from "./components/CodePanel";
import "./App.css";
import { BackEndAPI } from "./util/API";
import { History } from "./util/History";
import VariablePanel from "./components/VariablePanel";

function App() {
  const [histories, setHistories] = useState<History[]>([]);
  const [selectedHistory, setSelectedHistory] = useState<History>();
  const [selectedHistoryID, setSelectedHistoryID] = useState<number>();

  const [globalLoading, setGlobalLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  const [splitSizes1, setSplitSizes1] = useState([20, 80]);
  const [splitSizes2, setSplitSizes2] = useState([60, 40]);
  const [splitSizes3, setSplitSizes3] = useState([50, 50]);

  const [detailLoading, setDetailLoading] = useState(true);

  useEffect(() => {
    //initialize the states
    async function loadInitialData() {
      setGlobalLoading(true);
      try {
        const data = await BackEndAPI.getInitialData();
        setSelectedHistoryID(data.selectedID);
        setHistories(data.histories);
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

  useEffect(() => {
    //initialize the states
    async function loadHistoryDetail(selectedHistoryID: number) {
      if (!selectedHistoryID) {
        return;
      }
      console.log(selectedHistoryID);
      setDetailLoading(true);
      try {
        const data = await BackEndAPI.getHistoryDetail(selectedHistoryID);
        setSelectedHistory(data);
      } catch (e) {
        if (e instanceof Error) {
          setError(e.message);
        }
      } finally {
        setDetailLoading(false);
      }
    }
    loadHistoryDetail(selectedHistoryID!);
  }, [selectedHistoryID]);

  return (
    <>
      {error && (
        <>
          <div className="center-page">
            <p>{error}</p>
          </div>
        </>
      )}

      {!globalLoading && !error && !detailLoading && (
        <>
          <Toolbar selectedHistoryID={0} />
          <ReactSplit
            direction={SplitDirection.Horizontal}
            initialSizes={splitSizes1}
            onResizeFinished={(pairInd, newSizes) => {
              setSplitSizes1(newSizes);
            }}
          >
            <div className="tile-xy">
              <HistoryTree
                selectedHistoryID={selectedHistoryID}
                histories={histories}
                setSelectedHistory={setSelectedHistory}
                setSelectedHistoryID={setSelectedHistoryID}
              />
            </div>
            <ReactSplit
              direction={SplitDirection.Vertical}
              initialSizes={splitSizes2}
              onResizeFinished={(pairInd, newSizes) => {
                setSplitSizes2(newSizes);
              }}
            >
              <div className="tile-xy u-showbottom">
                <CodePanel selectedHistory={selectedHistory} />
              </div>
              <ReactSplit
                direction={SplitDirection.Horizontal}
                initialSizes={splitSizes3}
                onResizeFinished={(pairInd, newSizes) => {
                  setSplitSizes3(newSizes);
                }}
              >
                <div className="tile-xy">
                  <SearchPanel />
                </div>
                <div className="tile-xy">
                  <VariablePanel variables={selectedHistory!.variables!} />
                </div>
              </ReactSplit>
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
  );
}

export default App;
