/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 22:14:31
 * @LastEditTime: 2023-07-18 11:46:05
 * @FilePath: /src/components/CodePanel/ExecutedCodePanel.tsx
 * @Description: The panel to display code cells of the currently selected history
 */
import {useContext} from "react";
import {AppContext} from "../../App";
import SingleCell from "./SingleCell";

function ExecutedCodePanel() {
    const props = useContext(AppContext);

    const length = props!.selectedCommit!.historyExecCells.length;

    return (
        <div>
            {props!.selectedCommit!.historyExecCells.map((code, i) => (
                <div key={i}>
                    <SingleCell execNumber={(length - i).toString()} content={code.content} cssClassNames={"notebook"}/>
                    <br/>
                </div>
            ))}
        </div>
    );
}

export default ExecutedCodePanel;
