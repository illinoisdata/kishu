/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 22:14:31
 * @LastEditTime: 2023-07-18 11:46:05
 * @FilePath: /src/components/CodePanel/index.tsx
 * @Description: The panel to display code cells of the currently selected history
 */
import { History } from "../../util/History";
import SingleCell from "./SingleCell";

export interface CodePanelProps {
  selectedHistory: History | undefined;
}

function CodePanel(props: CodePanelProps) {
  return (
    <>
      {props.selectedHistory!.codes!.map((code) => (
        <>
          <SingleCell
            key={code.oid}
            execNumber={code.execNum}
            oid={code.oid}
            content={code.content}
          />
          <br />
        </>
      ))}
    </>
  );
}

export default CodePanel;
