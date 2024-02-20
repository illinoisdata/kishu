/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-16 11:49:19
 * @LastEditTime: 2023-07-29 11:45:44
 * @FilePath: /src/util/History.ts
 * @Description:inner representation of one history(i.e. commit)
 */
import { Cell } from "./Cell";
import { Variable } from "./Variable";
export interface Commit {
  oid: string;
  timestamp: string;
  parentOid: string;
  codeVersion: string;
  variableVersion: string;
  branchIds: string[];
  tags: string[];
  message:string;
}

export interface CommitDetail {
  commit: Commit;
  codes: Cell[]; //no need for get commit_graph
  variables: Variable[]; //no need for get commit_graph
  historyExecCells: Cell[];
}

