/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-18 14:27:43
 * @LastEditTime: 2023-07-18 14:37:03
 * @FilePath: /src/components/VariablePanel/index.tsx
 * @Description:
 */
import { Variable } from "../../util/Variable";
import React from "react";
export interface VariablePanelProps {
  variables: Variable[];
}
export default function VariablePanel(props: VariablePanelProps) {
  return (
    <div>
      <ul>
        {props.variables.map((variable) => (
          <li key={variable.oid}>
            {variable.variableName}:{variable.state}
          </li>
        ))}
      </ul>
    </div>
  );
}
