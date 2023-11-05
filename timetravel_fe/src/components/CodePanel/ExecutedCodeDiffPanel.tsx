/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 22:14:31
 * @LastEditTime: 2023-07-18 11:46:05
 * @FilePath: /src/components/CodePanel/ExecutedCodePanel.tsx
 * @Description: The panel to display code cells of the currently selected history
 */
import {useContext} from "react";
import {AppContext} from "../../App";
import SingleDiffCell from "./SingleDiffCell";


function ExecutedCodeDiffPanel() {
    const props = useContext(AppContext);
    return (
        <div>
            {props!.DiffCommitDetail?.executedCellDiffHunks.map((hunk, i) => {
                return <div
                    key={i}
                ><SingleDiffCell diffHunk={hunk}/><br/></div>
            })}
        </div>
    )
}

export default ExecutedCodeDiffPanel;
