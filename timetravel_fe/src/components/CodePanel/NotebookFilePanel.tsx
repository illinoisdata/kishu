/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 22:14:31
 * @LastEditTime: 2023-07-18 11:46:05
 * @FilePath: /src/components/CodePanel/ExecutedCodePanel.tsx
 * @Description: The panel to display code cells of the currently selected history
 */
import {useContext,} from "react";
import SingleCell from "./SingleCell";
import {AppContext} from "../../App";


function NotebookFilePanel() {
    const props = useContext(AppContext);
    return (
        <div>
            {props!.selectedCommit!.codes!.map((code, i) => (
                <div
                    key={i}
                >
                    <SingleCell execNumber={code.execNum} content={code.content} cssClassNames={"notebook"}/>
                    <br/>
                </div>
            ))}
        </div>
    );
}

export default NotebookFilePanel;
