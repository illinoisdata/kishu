/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-29 11:45:06
 * @LastEditTime: 2023-07-29 15:28:50
 * @FilePath: /src/util/parser.ts
 * @Description:
 */
import { Cell } from "./Cell";
import { Commit } from "./Commit";
import { Variable } from "./Variable";
export function parseAllCommits(object: any) {
  // console.log(object);
  const items = object["commits"];
  const commits: Commit[] = items.map(
    (item: any) =>
      ({
        oid: item["oid"],
        branchId: item["branch_id"],
        timestamp: item["timestamp"],
        parentBranchID: item["parent_branch_id"],
        parentOid: item["parent_oid"],
        tag: item["tag"],
      } as Commit)
  );
  const currentHead = object["head"]["commit_id"];
  const currentHeadBranch = object["head"]["branch_name"];

  return {
    commits: commits,
    currentHead: currentHead,
    currentHeadBranch: currentHeadBranch,
  };
}
export function parseCommitDetail(json: any) {
  // console.log(json);
  const tmp = json;
  console.log(tmp["cells"]);

  //calculate the max cell to be the execute cell
  let max = "-1";
  for (let i = 0; i < tmp["cells"].length; i++) {
    console.log(tmp["cells"][i]["exec_num"]);
    if (tmp["cells"][i]["exec_num"] === "None") {
      continue;
    } else if (parseInt(tmp["cells"][i]["exec_num"]) > parseInt(max)) {
      max = tmp["cells"][i]["exec_num"];
    }
  }

  const history: Commit = {
    oid: tmp["oid"],
    branchId: tmp["branch_id"],
    timestamp: tmp["timestamp"],
    parentBranchID: tmp["parent_branchID"],
    parentOid: tmp["parent_oid"],
    tag: tmp["tag"],
    codes: tmp["cells"].map(
      (item: any) =>
        ({
          content: item["content"],
          execNum: item["exec_num"] === "None" ? "-1" : item["exec_num"],
        } as Cell)
    ),
    execCell: max,
    variables: tmp["variables"].map((item: any) => recursiveGetVariable(item)),
  };
  return history;
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
        recursiveGetVariable(child)
      ),
    } as Variable;
  }
}
