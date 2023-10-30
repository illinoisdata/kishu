/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-27 15:17:43
 * @LastEditTime: 2023-07-27 18:13:26
 * @FilePath: /src/components/HistoryPanel/ContextMenu.tsx
 * @Description:
 */
import React, {useContext} from "react";
import {
    AppstoreOutlined,
    CalendarOutlined,
    EditOutlined,
} from "@ant-design/icons";
import {Menu} from "antd";
import type {MenuProps} from "antd/es/menu";
import {AppContext} from "../../App";

type MenuItem = Required<MenuProps>["items"][number];

function getItem(
    label: React.ReactNode,
    key?: React.Key | null,
    icon?: React.ReactNode,
    children?: MenuItem[],
): MenuItem {
    return {
        key,
        icon,
        children,
        label,
    } as MenuItem;
}

const items: MenuItem[] = [
    getItem("Add/Modify Tag for Selected History", "tag", <EditOutlined/>),
    getItem("Create Branch", "branch", <CalendarOutlined/>),
    getItem("RollBack to Selected History ", "rollback", <AppstoreOutlined/>, [
        getItem("Rollback Codes&Variable States", "both"),
        getItem("Rollback States", "states"),
    ]),
];

interface ContextMenuProps {
    x: number;
    y: number;
    onClose: () => void;
    setIsTagEditorOpen: React.Dispatch<React.SetStateAction<boolean>>; //set if the tag editor is open
    setIsBranchNameEditorOpen: any;
    setIsCheckoutWaitingModalOpen: any;
    setChooseCheckoutBranchModelOpen: any;
    setChckoutMode: any;
}

function ContextMenu({
                         x,
                         y,
                         onClose,
                         setIsTagEditorOpen,
                         setIsBranchNameEditorOpen,
                         setIsCheckoutWaitingModalOpen,
                         setChooseCheckoutBranchModelOpen,
                         setChckoutMode,
                     }: ContextMenuProps) {
    const props = useContext(AppContext);
    const onClickMenuItem: MenuProps["onClick"] = async ({key, domEvent}) => {
        onClose();
        domEvent.preventDefault();
        if (key === "tag") {
            setIsTagEditorOpen(true);
        } else if (key === "both") {
            if (props!.selectedCommit!.commit.branchIds.length === 0) {
                setIsCheckoutWaitingModalOpen(true);
                setChckoutMode("checkout codes and data");
            } else {
                setChooseCheckoutBranchModelOpen(true);
                setChckoutMode("checkout codes and data");
            }
        } else if (key === "branch") {
            setIsBranchNameEditorOpen(true);
        } else if (key === "states") {
            if (!props!.selectedCommit!.commit.branchIds) {
                setIsCheckoutWaitingModalOpen(true);
                setChckoutMode("checkout variables only");
            } else {
                setChooseCheckoutBranchModelOpen(true);
                setChckoutMode("checkout variables only");
            }
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
                    zIndex: 9999,
                }}
            >
                <Menu
                    style={{width: 300}}
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
