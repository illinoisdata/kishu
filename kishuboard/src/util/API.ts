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
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                branch_or_commit_id: branchID ? branchID : commitID,
                skip_notebook: "False"
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/checkout?${params.toString()}`);
        if (res.status !== 200) {
            throw new Error("rollback backend error, status != OK");
        }
    },


    async rollbackVariables(commitID: string, branchID?: string) {
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                branch_or_commit_id: branchID ? branchID : commitID,
                skip_notebook: "True"
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/checkout?${params.toString()}`);
        if (res.status !== 200) {
            throw new Error("rollback backend error, status != OK");
        }
    },

    async getCommitGraph() {
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/fe/commit_graph?${params.toString()}`);
        if (res.status !== 200) {
            throw new Error("get commit graph backend error, status != 200");
        }
        const data = await res.json();
        return parseCommitGraph(data);
    },

    async getCommitDetail(commitID: string) {
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                commit_id: commitID
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/fe/commit?${params.toString()}`);
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
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                commit_id: commitID,
                tag_name: newTag
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/tag?${params.toString()}`);
        if (res.status !== 200) {
            throw new Error("setting tags error, status != 200");
        }
    },

    async setMessage(commitID: string, newMessage: string) {
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                commit_id: commitID,
                new_message: newMessage
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/fe/edit_message?${params.toString()}`);
        if (res.status !== 200) {
            throw new Error("setting message error, status != 200");
        }
    },

    async deleteTag(tagID: string) {
        console.log("delete tag", tagID)
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                tag_name: tagID
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/delete_tag?${params.toString()}`);
        console.log("delete tag res", res)
        if (res.status !== 200) {
            throw new Error("delete tags error, status != 200");
        }
    },

    async editBranch(commitID: string, newBranchName: string, oldBranchName: string|undefined) {
        // message.info(`rollback succeeds`);
        if(oldBranchName){
            const params = new URLSearchParams(
                {
                    notebook_path: globalThis.NotebookPath!,
                    old_branch_name: oldBranchName,
                    new_branch_name: newBranchName
                }
            )
            const res = await fetch(`${BACKEND_URL}/api/rename_branch?${params.toString()}`);
            if (res.status !== 200) {
                throw new Error("edit branch error, status != 200");
            }
        }else{
            const params = new URLSearchParams(
                {
                    notebook_path: globalThis.NotebookPath!,
                    commit_id: commitID,
                    branch_name: newBranchName
                }
            )
            const res = await fetch(`${BACKEND_URL}/api/branch?${params.toString()}`);
            if (res.status !== 200) {
                throw new Error("create branch error, status != 200");
            }
        }
    },

    async deleteBranch(branchName: string) {
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                branch_name: branchName
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/delete_branch?${params.toString()}`);
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
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                from_commit_id: originID,
                to_commit_id: destID
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/fe/code_diff?${params.toString()}`);
        if (res.status !== 200) {
            throw new Error("get code diff error, status != 200");
        }
        const data = await res.json();
        return parseCodeDiff(data);
    },

    async getDataDiff(originID: string, destID: string){
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                from_commit_id: originID,
                to_commit_id: destID
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/fe/var_diff?${params.toString()}`);
        if (res.status !== 200) {
            throw new Error("get variable diff error, status != 200");
        }
        const data = await res.json();
        return parseVarDiff(data);
    },

    async getFilteredCommit(varName: string){
        const params = new URLSearchParams(
            {
                notebook_path: globalThis.NotebookPath!,
                variable_name: varName
            }
        )
        const res = await fetch(`${BACKEND_URL}/api/fe/find_var_change?${params.toString()}`);
        if (res.status !== 200) {
            throw new Error("get filtered commit error, status != 200");
        }
        const data = await res.json();
        return parseFilteredCommitIDs(data);
    },

    async getNotebookPath(notebookID: string):Promise<string> {
        const list = await this.getNotebookList()
        for (const item of list) {
            if (item.NotebookID === notebookID) {
                return item.notebookPath
            }
        }
        throw new Error("Invalid notebookID or notebook kernel is not running")
    }
};

export {BackEndAPI};
