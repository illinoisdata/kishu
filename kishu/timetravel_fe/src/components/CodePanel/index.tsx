/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 22:14:31
 * @LastEditTime: 2023-07-18 11:46:05
 * @FilePath: /src/components/CodePanel/index.tsx
 * @Description: The panel to display code cells of the currently selected history
 */
import { useContext } from "react";
import SingleCell from "./SingleCell";
import { AppContext } from "../../App";

function CodePanel() {
  const props = useContext(AppContext);
  return (
    <>
      {props!.selectedCommit!.codes!.map((code, i) => (
        <>
          <SingleCell
            key={i}
            execNumber={code.execNum}
            content={code.content}
          />
          <br />
        </>
      ))}
    </>
  );
}

export default CodePanel;
