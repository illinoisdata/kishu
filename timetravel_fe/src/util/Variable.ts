import React from "react";

/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-15 22:04:38
 * @LastEditTime: 2023-07-29 15:27:56
 * @FilePath: /src/util/Variable.ts
 * @Description:
 */
export interface Variable {
  key: React.ReactNode;
  variableName: string;
  state: string;
  type: string;
  size?: string;
  children: Variable[];
}
