/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-16 11:49:19
 * @LastEditTime: 2023-07-17 10:37:53
 * @FilePath: /src/util/History.ts
 * @Description:inner representation of one history(i.e. commit)
 */
import { Cell } from "./Cell";
import { Variable } from "./Variable";
export interface HistoryProps {
  oid: number;
  branchId: number;
  timestamp: string;
  parentBranchID: number;
  parentOid: number;
  branchName?: string;
  codes?: Cell[];
  variables?: Variable[];
  execCell?: number;
}
export class History {
  oid: number;
  branchId: number;
  timestamp: string;
  parentBranchID: number;
  parentOid: number;

  branchName: string | undefined;
  codes: Cell[] | undefined;
  variables: Variable[] | undefined;
  execCell: number | undefined;

  constructor(initializer: HistoryProps) {
    this.oid = initializer.oid;
    this.branchId = initializer.branchId;
    this.timestamp = initializer.timestamp;
    this.parentBranchID = initializer.parentBranchID;
    this.parentOid = initializer.parentOid;
    if (initializer.branchName) {
      this.branchName = initializer.branchName;
    }
    if (initializer.codes) {
      this.codes = initializer.codes;
    }
    if (initializer.variables) {
      this.variables = initializer.variables;
    }
    if (initializer.execCell) {
      this.execCell = initializer.execCell;
    }
  }
}
