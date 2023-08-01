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
} from "@ant-design/icons";
import { Menu, message } from "antd";
import type { MenuProps } from "antd/es/menu";
import TagEditor from "./TagEditor";

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
  getItem("Add/Modify Tag for Selected History", "tag", <MailOutlined />),
  getItem("Show All Histories", "show_all", <CalendarOutlined />),
  getItem("Show Only", "show_only", <AppstoreOutlined />, [
    getItem("Tagged Histories", "tag_only"),
    getItem("Searching Results", "search_only"),
    // getItem("Submenu", "sub1-2", null, [
    //   getItem("Option 5", "5"),
    //   getItem("Option 6", "6"),
    // ]),
  ]),
  // getItem("Navigation Three", "sub2", <SettingOutlined />, [
  //   getItem("Option 7", "7"),
  //   getItem("Option 8", "8"),
  //   getItem("Option 9", "9"),
  //   getItem("Option 10", "10"),
  // ]),
  // getItem(
  //   <a href="https://ant.design" target="_blank" rel="noopener noreferrer">
  //     Ant Design
  //   </a>,
  //   "link",
  //   <LinkOutlined />
  // ),
];

interface ContextMenuProps {
  x: number;
  y: number;
  onClose: () => void;
  setIsModalOpen: any;
}

function ContextMenu({ x, y, onClose, setIsModalOpen }: ContextMenuProps) {
  const onClickMenuItem: MenuProps["onClick"] = ({ key, domEvent }) => {
    onClose();
    domEvent.preventDefault();
    if (key === "tag") {
      setIsModalOpen(true);
    }
    message.info(key);
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
