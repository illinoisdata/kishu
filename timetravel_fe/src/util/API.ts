import {parseCommitGraph, parseCommitDetail, parseList, parseDiff} from "./parser";
import logger from "../log/logger";

/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 16:36:40
 * @LastEditTime: 2023-08-01 10:50:15
 * @FilePath: /src/util/API.ts
 * @Description:
 */
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';
const BackEndAPI = {
    async rollbackBoth(commitID: string, branchID?: string) {
        // message.info(`rollback succeeds`);
        let res;
        if (branchID) {
            res = await fetch(BACKEND_URL + "/checkout/" + globalThis.NotebookID! + "/" + branchID);
        } else {
            res = await fetch(BACKEND_URL + "/checkout/" + globalThis.NotebookID! + "/" + commitID);
        }
        if (res.status !== 200) {
            throw new Error("rollback backend error, status != OK");
        }
    },


    async rollbackVariables(commitID: string, branchID?: string) {
        // message.info(`rollback succeeds`);
        let res;
        if (branchID) {
            res = await fetch(BACKEND_URL + "/checkout/" + globalThis.NotebookID! + "/" + branchID + "?skip_notebook=True");
        } else {
            res = await fetch(BACKEND_URL + "/checkout/" + globalThis.NotebookID! + "/" + commitID + "?skip_notebook=True");
        }
        if (res.status !== 200) {
            throw new Error("rollback backend error, status != OK");
        }
        const data = await res.json();
    },

    async getCommitGraph() {
        const res = await fetch(BACKEND_URL + "/fe/commit_graph/" + globalThis.NotebookID!);
        if (res.status !== 200) {
            throw new Error("get commit graph backend error, status != 200");
        }
        const data = await res.json();
        return parseCommitGraph(data);
    },

    async getCommitDetail(commitID: string) {
        const res = await fetch(
            BACKEND_URL + "/fe/commit/" + globalThis.NotebookID! + "/" + commitID,
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
            BACKEND_URL + "/tag/" +
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
        const data = await res.json();

    },

    async createBranch(commitID: string, newBranchname: string) {
        // message.info(`rollback succeeds`);
        const res = await fetch(
            BACKEND_URL + "/branch/" +
            globalThis.NotebookID! +
            "/" +
            newBranchname +
            "?commit_id=" +
            commitID,
        );
        if (res.status !== 200) {
            throw new Error("create branch error, status != 200");
        }
        const data = await res.json();
    },

    async getNotebookList() {
        const res = await fetch(BACKEND_URL + "/list");
        if (res.status !== 200) {
            throw new Error("get commit detail error, status != 200");
        }
        const data = await res.json()
        return parseList(data)

    },

    async getDiff(originID: string,destID: string) {
        const res = await fetch(
            BACKEND_URL + "/fe/diff/" + globalThis.NotebookID! + "/" + originID + "/" + destID,
        );
        if (res.status !== 200) {
            throw new Error("get diff error, status != 200");
        }
        const data = await res.json();
        return parseDiff(data);

    }
};

export {BackEndAPI};
