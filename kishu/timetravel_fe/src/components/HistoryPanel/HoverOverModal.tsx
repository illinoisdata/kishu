/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-27 15:17:43
 * @LastEditTime: 2023-07-27 18:13:26
 * @FilePath: /src/components/HistoryPanel/ContextMenu.tsx
 * @Description:
 */
import { message } from "antd";
import React, { useContext, useState } from "react";
import ReactDOM from "react-dom";

export interface HoverOverProps {
  x: number;
  y: number;
  timestamp: string;
}

function HoverPopup({ x, y, timestamp }: HoverOverProps) {
  return (
    <>
      <div
        style={{
          position: "fixed",
          top: y,
          left: x,
          zIndex: 9999,
        }}
      >
        {timestamp}
      </div>
    </>
  );
}

function MyFunctionalComponent() {
  return (
    <div>
      <h1>Hello, I'm a functional component!</h1>
    </div>
  );
}

export default HoverPopup;
