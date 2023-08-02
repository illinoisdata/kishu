/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-27 15:17:43
 * @LastEditTime: 2023-07-27 18:13:26
 * @FilePath: /src/components/HistoryPanel/ContextMenu.tsx
 * @Description:
 */
import React, { useState } from "react";
import ReactDOM from "react-dom";
import {
  AppstoreOutlined,
  CalendarOutlined,
  LinkOutlined,
  MailOutlined,
  SettingOutlined,
  EditOutlined,
} from "@ant-design/icons";
import { Menu, message } from "antd";
import type { MenuProps } from "antd/es/menu";
import TagEditor from "./TagEditor";
import { Judger } from "../../util/JudgeFunctions";
import { History } from "../../util/History";

type MenuItem = Required<MenuProps>["items"][number];

function getItem(
  label: React.ReactNode,
  key?: React.Key | null,
  icon?: React.ReactNode,
  children?: MenuItem[]
): MenuItem {
  return {
    key,
    icon,
    children,
    label,
  } as MenuItem;
}

const items: MenuItem[] = [
  getItem("Add/Modify Tag for Selected History", "tag", <EditOutlined />),
  getItem("Show All Histories", "show_all", <CalendarOutlined />),
  getItem("Show Only", "show_only", <AppstoreOutlined />, [
    getItem("Tagged Histories", "tag_only"),
    getItem("Searching Results", "search_only"),
  ]),
  getItem("RollBack to Selected History ", "rollback", <AppstoreOutlined />, [
    getItem("Rollback Codes&Variable States", "both"),
    getItem("Rollback Codes", "codes"),
    getItem("Rollback States", "states"),
  ]),
];

interface ContextMenuProps {
  x: number;
  y: number;
  onClose: () => void;
  setIsModalOpen: React.Dispatch<React.SetStateAction<boolean>>; //set if the tag editor is open
  setJudgeFunctionID: any;
  setIsGroupFolded: any;
  judgeFunctionID: number;
  isGroupFolded?: Map<string, boolean>;
}

function ContextMenu({
  x,
  y,
  onClose,
  setIsModalOpen,
  setJudgeFunctionID,
  setIsGroupFolded,
  judgeFunctionID,
  isGroupFolded,
}: ContextMenuProps) {
  const onClickMenuItem: MenuProps["onClick"] = ({ key, domEvent }) => {
    onClose();
    domEvent.preventDefault();
    if (key === "tag") {
      setIsModalOpen(true);
    } else if (key === "tag_only") {
      if (judgeFunctionID === 0) {
        let newIsGroupFolded = new Map<string, boolean>();
        isGroupFolded!.forEach((value, key, map) => {
          newIsGroupFolded.set(key, true);
        });
        setIsGroupFolded(newIsGroupFolded);
      } else {
        setJudgeFunctionID(0);
      }
    } else if (key === "search_only") {
      if (judgeFunctionID === 2) {
        let newIsGroupFolded = new Map<string, boolean>();
        isGroupFolded!.forEach((value, key, map) => {
          newIsGroupFolded.set(key, true);
        });
        setIsGroupFolded(newIsGroupFolded);
      } else {
        setJudgeFunctionID(2);
      }
    } else if (key === "show_all") {
      setJudgeFunctionID(1);
    }
    // message.info(key);
  };

  return (
    <>
      <div
        style={{
          position: "fixed",
          top: y,
          left: x,
        }}
      >
        <Menu
          style={{ width: 300 }}
          defaultSelectedKeys={["1"]}
          defaultOpenKeys={["sub1"]}
          mode={"vertical"}
          items={items}
          onClick={onClickMenuItem}
        />
      </div>
    </>
  );
}

export default ContextMenu;
