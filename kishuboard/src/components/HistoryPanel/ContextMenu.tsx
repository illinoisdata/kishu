import React, {useContext} from "react";
import {
    AppstoreOutlined,
    CalendarOutlined,
    EditOutlined,
} from "@ant-design/icons";
import {Menu, message} from "antd";
import type {MenuProps} from "antd/es/menu";
import {AppContext, OperationModelContext} from "../../App";
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
    items.push(getItem("Add Tag for Selected Commit", "tag", <EditOutlined/>))
    items.push(getItem("Create Branch", "branch", <CalendarOutlined/>))
    items.push(getItem("Checkout", "rollback", <AppstoreOutlined/>, [
        getItem("Variables", "states"),
        getItem("Variables + Code", "both"),
    ]))
    items.push(getItem("Edit Commit Message", "message", <EditOutlined/>))
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
    refreshGraphHandler: any;
}

function ContextMenu({
                         x,
                         y,
                         onClose,
                            refreshGraphHandler,
                     }: ContextMenuProps) {
    const props = useContext(AppContext);
    const operationModelContext = useContext(OperationModelContext)!
    const items = getItems(props!.selectedCommit?.commit.tags, props!.selectedCommit?.commit.branchIds);
    const onClickMenuItem: MenuProps["onClick"] = async ({key, domEvent}) => {
        onClose();
        domEvent.preventDefault();
        if (key === "tag") {
            operationModelContext.setIsTagEditorOpen(true);
        }else if(key === "message"){
            operationModelContext.setIsMessageEditorOpen(true);
        } else if (key === "both") {
            if (props!.selectedCommit!.commit.branchIds.length == 0) {
                operationModelContext.setIsCheckoutWaitingModalOpen(true);
                operationModelContext.setCheckoutMode("checkout codes and data");
            } else if(props!.selectedCommit!.commit.branchIds.length ===  1){
                operationModelContext.setIsCheckoutWaitingModalOpen(true);
                operationModelContext.setCheckoutBranchID(props!.selectedCommit!.commit.branchIds[0]);
                operationModelContext.setCheckoutMode("checkout codes and data");
            }
            else {
                operationModelContext.setChooseCheckoutBranchModalOpen(true);
                operationModelContext.setCheckoutMode("checkout codes and data");
            }
        } else if (key === "branch") {
            operationModelContext.setIsBranchNameEditorOpen(true);
        } else if (key === "states") {
            if (props!.selectedCommit!.commit.branchIds.length === 0) {
                operationModelContext.setIsCheckoutWaitingModalOpen(true);
                operationModelContext.setCheckoutMode("checkout variables only");
            } else if(props!.selectedCommit!.commit.branchIds.length ===  1){
                operationModelContext.setIsCheckoutWaitingModalOpen(true);
                operationModelContext.setCheckoutBranchID(props!.selectedCommit!.commit.branchIds[0]);
                operationModelContext.setCheckoutMode("checkout variables only");
            }
            else {
                operationModelContext.setChooseCheckoutBranchModalOpen(true);
                operationModelContext.setCheckoutMode("checkout variables only");
            }
        } else if (key.startsWith("Delete Branch")){
            let branchName = getWordAfter(key, "Delete Branch");
            if(branchName === props?.currentHeadBranch){
                message.warning("You cannot delete the current branch")
                return
            }
            await BackEndAPI.deleteBranch(branchName!);
            refreshGraphHandler()
        } else if (key.startsWith("Delete Tag")){
            let tagName = getWordAfter(key, "Delete Tag");
            await BackEndAPI.deleteTag(tagName!);
            //refresh the graph
            refreshGraphHandler()
        } else if (key.startsWith("Edit Branch")){
            let branchName = getWordAfter(key, "Edit Branch");
            operationModelContext.setIsBranchNameEditorOpen(true);
            operationModelContext.setBranchNameToBeEdit(branchName!)
        } else if(key.startsWith("Edit Tag")){
            let tagName = getWordAfter(key, "Edit Tag");
            operationModelContext.setIsTagEditorOpen(true);
            operationModelContext.setTagNameToBeEdit(tagName!)
        }
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


function getWordAfter(inputString: string, prefix: string): string | null {
    const words = inputString.trim().split(' ');
    const prefixWords = prefix.trim().split(' ');

    // Check if there are any words in the string
    if (words.length === 0) {
        return null; // No words found, return null or an appropriate value
    }

    //check if the prefixWords is valid
    for (let i = 0; i < prefixWords.length; i++) {
        if (i >= words.length || prefixWords[i] !== words[i]) {
            return null;
        }
    }

    // Return the last words
    return words.slice(prefixWords.length).join(' ');
}


export default ContextMenu;
