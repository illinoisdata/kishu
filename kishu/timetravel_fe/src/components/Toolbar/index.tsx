/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 10:20:09
 * @LastEditTime: 2023-07-15 22:18:28
 * @FilePath: /src/components/Toolbar/index.tsx
 * @Description: toolBar includes rollback buttons, and the menu to choose rollback type.
 */
import React, { SyntheticEvent, useContext, useState } from "react";
import "./toolbar.css";
import "../utility.css";
import { DownOutlined, SearchOutlined } from "@ant-design/icons";
import type { MenuProps } from "antd";
import { Button, Space, message, Dropdown, Input, ConfigProvider } from "antd";
import { log } from "console";
import { BackEndAPI } from "../../util/API";
import DropdownBranch from "./DropDownBranch";
import Search from "antd/es/input/Search";
import { AppContext } from "../../App";

// export interface Props {
//   currentBranchID: string;
//   branchIDs: Set<String>;
//   setSelectedBranchID: any;
//   setSelectedCommitID: any;
// }

enum RollBackType {
  "BOTH" = 1,
  "CODES" = 2,
  "VARIABLES" = 3,
}

function Toolbar() {
  const props = useContext(AppContext);
  return (
    <>
      <ConfigProvider
        theme={{
          token: {
            colorBgContainer: "#588157",
            colorTextPlaceholder: "white",
            colorTextBase: "white",
          },
          components: {
            Button: {
              colorPrimary: "#344E41",
              colorText: "white",
            },
          },
        }}
      >
        {" "}
        <div className="toolBar">
          <div>
            {/* <Space wrap>branch name : </Space> */}
            <DropdownBranch />
          </div>
          <Search
            placeholder="input search text"
            enterButton
            style={{ backgroundColor: "#D5BDAF" }}
          />
          {/* onSearch={} */}
        </div>
      </ConfigProvider>
    </>
  );
}

export default Toolbar;
