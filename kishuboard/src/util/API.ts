import {
    parseCommitGraph,
    parseCommitDetail,
    parseList,
    parseCodeDiff,
    parseFilteredCommitIDs,
    parseVarDiff
} from "./parser";
import {logger} from "../log/logger";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';
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
        logger.silly("commit detail before parse", data);
        return parseCommitDetail(data);
    },

    async setTag(commitID: string, newTag: string) {
        const res = await fetch(
            BACKEND_URL + "/api/tag/" +
            globalThis.NotebookID! +
            "/" +
            newTag +
            "?commit_id=" +
            commitID,
            //
            // "&message=" +
            // newTag,
        );
        if (res.status !== 200) {
            throw new Error("setting tags error, status != 200");
        }
    },

    async createBranch(commitID: string, newBranchname: string) {
        // message.info(`rollback succeeds`);
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
    }
};

export {BackEndAPI};
