import {Cell} from "./Cell";
import {Commit, CommitDetail} from "./Commit";
import {Variable} from "./Variable";
import {Session} from "./Session";
import {DiffHunk} from "./DiffHunk";
import {DiffCommitDetail} from "./DiffCommitDetail";
import logger from "../log/logger";

export function parseList(object: any) {
    logger.silly("session list from backend",object)
    const _sessions = object["sessions"];
    return _sessions.map(
        (item: any) => (
            {
                NotebookID: item["notebook_id"],
                kernelID: item["kernel_id"],
                notebookPath: item["notebook_path"],
                isAlive: item["is_alive"],
            }
        ) as Session
    )
}

//parse and sort the data from backend
export function parseCommitGraph(object: any) {
    logger.silly("git graph from backend", object)
    const items = object["commits"];
    const commits: Commit[] = items.map(
        (item: any) =>
            ({
                oid: item["oid"],
                // branchIds: item["branch_ids"],
                branchIds: item["branches"],
                timestamp: item["timestamp"],
                parentOid: item["parent_oid"],
                tags: item["tags"],
                codeVersion: item["code_version"],
                variableVersion: item["var_version"],
            }) as Commit,
    );
    const currentHead = object["head"]["commit_id"];
    const currentHeadBranch = object["head"]["branch_name"];
    //sorted by time, from newest to oldest
    commits.sort((a, b) => {
        const timestampA = new Date(a.timestamp).getTime();
        const timestampB = new Date(b.timestamp).getTime();
        return timestampB - timestampA;
    });

    return {
        commits: commits,
        currentHead: currentHead,
        currentHeadBranch: currentHeadBranch,
    };
}

export function parseCommitDetail(json: any) {
    // logger.silly("commit detail from backend",json)
    const item = json["commit"];

    const commitDetail: CommitDetail = {
        commit: {
            codeVersion: item["code_version"],
            variableVersion: item["variable_version"],
            oid: item["oid"],
            timestamp: item["timestamp"],
            parentOid: item["parent_oid"],
            branchIds: item["branches"],
            tags: item["tags"],
        },
        codes: json["cells"].map(
            (item: any) =>
                ({
                    content: item["content"],
                    execNum: item["exec_num"] === "None" ? "-1" : item["exec_num"],
                }) as Cell,
        ),
        variables: json["variables"].map((variable: any) =>
            recursiveGetVariable(variable),
        ),
        // historyExecCells: json["cells"]
        historyExecCells: json["executed_cells"].reverse().map(
            (item: any) => ({
                content: item,
                execNum: "-1"
            }) as Cell
        ),
    };
    return commitDetail;
}

function recursiveGetVariable(item: any): Variable {
    if (!item["children"] || item["children"].length === 0) {
        return {
            key: item["variable_name"],
            variableName: item["variable_name"],
            state: (item["state"] as string).replaceAll("\n", "\\n"),
            type: item["type"],
            size: item["size"],
            html: item["html"],
        } as Variable;
    } else {
        return {
            key: item["variable_name"],
            variableName: item["variable_name"],
            state: (item["state"] as string).replaceAll("\n", "\\n"),
            type: item["type"],
            size: item["size"],
            html: item["html"],
            children: item["children"].map((child: any) =>
                recursiveGetVariable(child),
            ),
        } as Variable;
    }
}

export function parseDiff(json: any) {
    logger.silly("diff from backend",json)
    const _notebook_cells_diff = json["notebook_cells_diff"];
    const _executed_cells_diff = json["executed_cells_diff"];
    let notebookCellDiffHunks: DiffHunk[] = _notebook_cells_diff.map((item: any) => parseDiffHunk(item));
    let executedCellDiffHunks: DiffHunk[] = _executed_cells_diff.map((item: any) => parseDiffHunk(item)).reverse();
    return {
        notebookCellDiffHunks: notebookCellDiffHunks,
        executedCellDiffHunks: executedCellDiffHunks
    } as DiffCommitDetail;
}

function parseDiffHunk(json: any) {
    const _option = json["option"];
    const _content = json["content"];
    const _sub_diff_hunks = json["sub_diff_hunks"];
    return {
        option: _option,
        content: _content,
        subDiffHunks: _sub_diff_hunks?.map((item: any) => parseDiffHunk(item))
    } as DiffHunk;
}
