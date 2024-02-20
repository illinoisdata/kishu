import {
    parseCommitGraph,
    parseCommitDetail,
    parseList,
    parseCodeDiff,
    parseFilteredCommitIDs,
    parseVarDiff
} from "./parser";
import {logger} from "../log/logger";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:4999';
const BackEndAPI = {
    async rollbackBoth(commitID: string, branchID?: string) {
        // message.info(`rollback succeeds`);
        let res;
        if (branchID) {
            res = await fetch(BACKEND_URL + "/api/checkout/" + globalThis.NotebookID! + "/" + branchID);
        } else {
            res = await fetch(BACKEND_URL + "/api/checkout/" + globalThis.NotebookID! + "/" + commitID);
        }
        if (res.status !== 200) {
            throw new Error("rollback backend error, status != OK");
        }
    },


    async rollbackVariables(commitID: string, branchID?: string) {
        // message.info(`rollback succeeds`);
        let res;
        if (branchID) {
            res = await fetch(BACKEND_URL + "/api/checkout/" + globalThis.NotebookID! + "/" + branchID + "?skip_notebook=True");
        } else {
            res = await fetch(BACKEND_URL + "/api/checkout/" + globalThis.NotebookID! + "/" + commitID + "?skip_notebook=True");
        }
        if (res.status !== 200) {
            throw new Error("rollback backend error, status != OK");
        }
    },

    async getCommitGraph() {
        const res = await fetch(BACKEND_URL + "/api/fe/commit_graph/" + globalThis.NotebookID!);
        if (res.status !== 200) {
            throw new Error("get commit graph backend error, status != 200");
        }
        const data = await res.json();
        return parseCommitGraph(data);
    },

    async getCommitDetail(commitID: string) {
        const res = await fetch(
            BACKEND_URL + "/api/fe/commit/" + globalThis.NotebookID! + "/" + commitID,
        );
        if (res.status !== 200) {
            throw new Error("get commit detail error, status != 200");
        }
        const data = await res.json();
        console.log("commit detail", data)
        logger.silly("commit detail before parse", data);
        return parseCommitDetail(data);
    },

    async setTag(commitID: string, newTag: string,oldTag?:string) {
        if(oldTag){
            await this.deleteTag(oldTag)
        }
        const res = await fetch(
            BACKEND_URL + "/api/tag/" +
            globalThis.NotebookID! +
            "/" +
            newTag +
            "?commit_id=" +
            commitID,
        );
        if (res.status !== 200) {
            throw new Error("setting tags error, status != 200");
        }
    },

    async setMessage(commitID: string, newMessage: string) {
        const res = await fetch(
            BACKEND_URL + "/api/fe/edit_message/" +
            globalThis.NotebookID! +
            "/" +
            commitID +
            "/" +
            newMessage,
        );
        if (res.status !== 200) {
            throw new Error("setting message error, status != 200");
        }
    },

    async changeTag(oleName: string, newName: string) {
        const res = await fetch(
            BACKEND_URL + "/change_tag/" +
            globalThis.NotebookID! +
            "/" +
            oleName +
            "?new_name=" +
            newName,
        );
        if (res.status !== 200) {
            throw new Error("change tags error, status != 200");
        }

    },

    async deleteTag(tagID: string) {
        console.log("delete tag", tagID)
        const res = await fetch(
            BACKEND_URL + "/api/delete_tag/" +
            globalThis.NotebookID! +
            "/" +
            tagID,
        );
        console.log("delete tag res", res)
        if (res.status !== 200) {
            throw new Error("delete tags error, status != 200");
        }
    },

    async editBranch(commitID: string, newBranchname: string, oldBranchName: string|undefined) {
        // message.info(`rollback succeeds`);
        if(oldBranchName){
            const res = await fetch(
                BACKEND_URL + "/api/rename_branch/" +
                globalThis.NotebookID! +
                "/" + oldBranchName + "/" + newBranchname
            );
            if (res.status !== 200) {
                throw new Error("edit branch error, status != 200");
            }
        }else{
            const res = await fetch(
                BACKEND_URL + "/api/branch/" +
                globalThis.NotebookID! +
                "/" +
                newBranchname +
                "?commit_id=" +
                commitID,
            );
            if (res.status !== 200) {
                throw new Error("create branch error, status != 200");
            }
        }
    },

    async deleteBranch(branchID: string) {
        // message.info(`rollback succeeds`);
        const res = await fetch(
            BACKEND_URL + "/api/delete_branch/" +
            globalThis.NotebookID! +
            "/" +
            branchID,
        );
        if (res.status !== 200) {
            throw new Error("delete branch error, status != 200");
        }
    },

    async getNotebookList() {
        const res = await fetch(BACKEND_URL + "/api/list");
        if (res.status !== 200) {
            throw new Error("get commit detail error, status != 200");
        }
        const data = await res.json()
        return parseList(data)

    },

    async getCodeDiff(originID: string, destID: string) {
        const res = await fetch(
            BACKEND_URL + "/api/fe/code_diff/" + globalThis.NotebookID! + "/" + originID + "/" + destID,
        );
        if (res.status !== 200) {
            throw new Error("get code diff error, status != 200");
        }
        const data = await res.json();
        return parseCodeDiff(data);
    },

    async getDataDiff(originID: string, destID: string){
        const res = await fetch(
            BACKEND_URL + "/api/fe/var_diff/" + globalThis.NotebookID! + "/" + originID + "/" + destID,
        );
        if (res.status !== 200) {
            throw new Error("get variable diff error, status != 200");
        }
        const data = await res.json();
        return parseVarDiff(data);
    },

    async getFilteredCommit(varName: string){
        const res = await fetch(
            BACKEND_URL + "/api/fe/find_var_change/" + globalThis.NotebookID! + "/" + varName,
        );
        if (res.status !== 200) {
            throw new Error("get filtered commit error, status != 200");
        }
        const data = await res.json();
        return parseFilteredCommitIDs(data);
    },

    async getNoteBookName(notebookID: string):Promise<string> {
        const list = await this.getNotebookList()
        for (const item of list) {
            if (item.NotebookID === notebookID) {
                // get the last part of the path
                return item.notebookPath.split("/").pop()!
            }
        }
        throw new Error("Invalid notebookID or notebook kernel is not running")
    }
};

export {BackEndAPI};
