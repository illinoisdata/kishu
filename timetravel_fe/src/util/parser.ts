/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-29 11:45:06
 * @LastEditTime: 2023-07-29 15:28:50
 * @FilePath: /src/util/parser.ts
 * @Description:
 */
import { Cell } from "./Cell";
import { Commit, CommitDetail } from "./Commit";
import { Variable } from "./Variable";

//parse and sort the data from backend
export function preprocessCommitGraph(object: any) {
  console.log("git graph from backend");
  console.log(object);
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
  console.log("commit detail from backend");
  console.log(json);
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
    historyExecCells: [],
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
    } as Variable;
  } else {
    return {
      key: item["variable_name"],
      variableName: item["variable_name"],
      state: (item["state"] as string).replaceAll("\n", "\\n"),
      type: item["type"],
      size: item["size"],
      children: item["children"].map((child: any) =>
        recursiveGetVariable(child),
      ),
    } as Variable;
  }
}
