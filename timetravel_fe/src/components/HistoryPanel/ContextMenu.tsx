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
import {BackEndAPI} from "../../util/API";

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

function getTagChildrenItem(tag: string): MenuItem[] {
    return [
        getItem("Delete Tag " + tag, "Delete Tag " + tag),
        getItem("Edit Tag " + tag, "Edit Tag " + tag),
    ]
}

function getBranchChildrenItem(branch: string): MenuItem[] {
    return [
        getItem("Delete Branch " + branch, "Delete Branch " + branch),
        getItem("Edit Branch " + branch, "Edit Branch " + branch),
    ]
}

function getItems(tags: string[]|undefined, branches: string[]|undefined): MenuItem[] {
    let items: MenuItem[] = [];
    items.push(getItem("Add Tag for Selected History", "tag", <EditOutlined/>))
    items.push(getItem("Create Branch", "branch", <CalendarOutlined/>))
    items.push(getItem("RollBack to Selected History ", "rollback", <AppstoreOutlined/>, [
        getItem("Checkout Codes&Variables", "both"),
        getItem("Rollback Executions", "states"),
    ]))
    if(tags){
        for (let tag of tags) {
            items.push(getItem("Tag " + tag, "Tag " + tag, <EditOutlined/>, getTagChildrenItem(tag)));
        }
    }
    if(branches){
        for (let branch of branches) {
            items.push(getItem("Branch " + branch, "Branch " + branch, <EditOutlined/>, getBranchChildrenItem(branch)));
        }
    }
    return items;
}

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
    const items = getItems(props!.selectedCommit?.commit.tags, props!.selectedCommit?.commit.branchIds);
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
            if (props!.selectedCommit!.commit.branchIds.length === 0) {
                setIsCheckoutWaitingModalOpen(true);
                setChckoutMode("checkout variables only");
            } else {
                setChooseCheckoutBranchModelOpen(true);
                setChckoutMode("checkout variables only");
            }
        } else if (key.startsWith("Delete Branch")){
            let branchName = getLastWord(key);
            await BackEndAPI.deleteBranch(branchName!);
        } else if (key.startsWith("Delete Tag")){
            let tagName = getLastWord(key);
            // await BackEndAPI.deleteTag(tagName!);
        } else if (key.startsWith("Edit Branch")){
            let branchName = getLastWord(key);
            setIsBranchNameEditorOpen(true);
            // props!.setBranchNameToEdit(branchName!);
            // await BackEndAPI.editBranch(branchName!);
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


function getLastWord(inputString: string): string | null {
    // Trim the input string to remove leading and trailing spaces
    const trimmedString = inputString.trim();

    // Split the trimmed string into words using spaces as the separator
    const words = trimmedString.split(' ');

    // Check if there are any words in the string
    if (words.length === 0) {
        return null; // No words found, return null or an appropriate value
    }

    // Return the last word
    return words[words.length - 1];
}


export default ContextMenu;
