/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-15 22:04:04
 * @LastEditTime: 2023-07-17 10:39:03
 * @FilePath: /src/util/Cell.ts
 * @Description:
 */
export interface CellProps {
  oid: number;
  version: number;
  content: string;
  execNum: number;
}

export class Cell {
  oid: number;
  version: number;
  content: string;
  execNum: number;

  constructor(initializer: CellProps) {
    this.oid = initializer.oid;
    this.version = initializer.version;
    this.content = initializer.content;
    this.execNum = initializer.execNum;
  }
}
