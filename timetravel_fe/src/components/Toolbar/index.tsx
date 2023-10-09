/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 10:20:09
 * @LastEditTime: 2023-07-15 22:18:28
 * @FilePath: /src/components/Toolbar/index.tsx
 * @Description: toolBar includes rollback buttons, and the menu to choose rollback type.
 */
import React, { SyntheticEvent, useState } from "react";
import "./toolbar.css";
import "../utility.css";
import { DownOutlined } from "@ant-design/icons";
import type { MenuProps } from "antd";
import { Dropdown, Space, message } from "antd";
import { log } from "console";
import { BackEndAPI } from "../../util/API";

export interface Props {
  selectedHistoryID: number;
}

enum RollBackType {
  "BOTH" = 1,
  "CODES" = 2,
  "VARIABLES" = 3,
}

function Toolbar({ selectedHistoryID }: Props) {
  const [loading, setLoading] = useState<boolean>(false);
  const [rollbackType, setRollbackType] = useState(RollBackType.BOTH);

  async function enterLoading() {
    setLoading(true);
    try {
      if (rollbackType === RollBackType.BOTH) {
        await BackEndAPI.rollbackBoth(selectedHistoryID);
      } else if (rollbackType === RollBackType.CODES) {
        await BackEndAPI.rollbackCodes(selectedHistoryID);
      } else {
        await BackEndAPI.rollbackVariables(selectedHistoryID);
      }
      message.info("rollback succeed");
    } catch (e) {
      if (e instanceof Error) {
        message.info(e.message);
      }
    } finally {
      setLoading(false);
    }
  }

  const onClickMenuItem: MenuProps["onClick"] = ({ key }) => {
    setRollbackType(Number(key));
  };

  //menu to choose rollback type
  const items: MenuProps["items"] = [
    {
      key: "1",
      label: "rollback both",
    },
    {
      key: "2",
      label: "rollback codes",
    },
    {
      key: "3",
      label: "rollback variables",
    },
  ];

  return (
    <>
      <div className="toolBar">
        <Space wrap>kishu_timeTravel</Space>
        <div>
          <Space wrap>
            <Dropdown.Button
              type="primary"
              icon={<DownOutlined />}
              loading={loading}
              menu={{
                items,
                onClick: onClickMenuItem,
                selectable: true,
                defaultSelectedKeys: ["1"],
              }}
              onClick={() => enterLoading()}
            >
              Submit Rollback
            </Dropdown.Button>
          </Space>
        </div>
      </div>
    </>
  );
}

export default Toolbar;
