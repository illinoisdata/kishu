/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 10:34:27
 * @LastEditTime: 2023-07-14 16:56:02
 * @FilePath: /src/App.tsx
 * @Description:
 */
import React from "react";
import "./App.css";
import ReactSplit, { SplitDirection } from "@devbookhq/splitter";
// import { useEffect, useState } from "react";
import Toolbar from "./components/Toolbar";
import HistoryTree from "./components/HistoryPanel/HistoryTree";
import SearchPanel from "./components/SearchPanel";
import CodePanel from "./components/CodePanel";
import "./App.css";

function App() {
  return (
    //
    <>
      <Toolbar selectedHistoryID={0} />
      <ReactSplit direction={SplitDirection.Horizontal} initialSizes={[20, 80]}>
        <div className="tile-xy">
          <HistoryTree />
        </div>
        <ReactSplit direction={SplitDirection.Vertical}>
          <div className="tile-xy u-showbottom">
            <CodePanel />
          </div>
          <ReactSplit direction={SplitDirection.Horizontal}>
            <div className="tile-xy">
              <SearchPanel />
            </div>
            <div className="tile-xy">variable preview</div>
          </ReactSplit>
        </ReactSplit>
      </ReactSplit>
    </>
  );
}

export default App;
