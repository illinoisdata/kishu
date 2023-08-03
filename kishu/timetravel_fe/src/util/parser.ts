/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-29 11:45:06
 * @LastEditTime: 2023-07-29 15:28:50
 * @FilePath: /src/util/parser.ts
 * @Description:
 */
import { Cell } from "./Cell";
import { History } from "./History";
import { Variable } from "./Variable";
export function parseAllCommits(json: any) {
  // console.log("entered");
  console.log(json);
  const items = json["Commits"];
  const histories: History[] = items.map(
    (item: any) =>
      ({
        oid: item["oid"],
        branchId: item["branch_id"],
        timestamp: item["timestamp"],
        parentBranchID: item["parent_branchID"],
        parentOid: item["parent_oid"],
        tag: item["tag"],
      } as History)
  );
  return histories;
}
export function parseCommitDetail(json: any) {
  console.log(json);
  const tmp = json;
  const history: History = {
    oid: tmp["oid"],
    branchId: tmp["branch_id"],
    timestamp: tmp["timestamp"],
    parentBranchID: tmp["parent_branchID"],
    parentOid: tmp["parent_oid"],
    tag: tmp["tag"],
    execCell: tmp["exec_num"],
    codes: tmp["cells"].map(
      (item: any) =>
        ({
          content: item["content"],
          execNum: item["exec_num"],
        } as Cell)
    ),
    variables: tmp["variables"].map((item: any) => recursiveGetVariable(item)),
  };
  return history;
}

function recursiveGetVariable(item: any): Variable {
  if (!item["children"]) {
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
