/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 10:34:27
 * @LastEditTime: 2023-08-01 09:38:18
 * @FilePath: /src/ExecutedCodePanel.tsx
 * @Description:
 */
import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
import {BrowserRouter, Route, Routes} from "react-router-dom";
import Menu from "./Menu";
import {ConfigProvider} from "antd";

function UserRouter() {
    return (
        <ConfigProvider
      theme={{
        token: {
          fontFamily: 'Fira Sans'
        }
      }}
    >
        <BrowserRouter>
            <Routes>
                <Route path="/" Component={Menu}/>
                <Route path="/:notebookID" Component={App}/>
            </Routes>
        </BrowserRouter>
        </ConfigProvider>
    );
}


const root = ReactDOM.createRoot(
    document.getElementById("root") as HTMLElement,
);
root.render(<UserRouter/>);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
