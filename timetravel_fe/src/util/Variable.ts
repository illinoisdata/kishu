/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-15 22:04:38
 * @LastEditTime: 2023-07-17 10:44:38
 * @FilePath: /src/util/Variable.ts
 * @Description:
 */
export interface VariableProps {
  oid: number;
  variableName: string;
  version: number;
  state: string;
}
export class Variable {
  oid: number;
  variableName: string;
  version: number;
  state: string;
  constructor(initializer: VariableProps) {
    this.oid = initializer.oid;
    this.variableName = initializer.variableName;
    this.version = initializer.version;
    this.state = initializer.state;
  }
}
