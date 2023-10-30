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


function NotebookFileDiffPanel() {
    const props = useContext(AppContext);

    // let result = props!.DiffCommitDetail?.notebookCellDiffHunks.map((hunk, i) => {
    //
    //     if (hunk.option == "Origin_only") {
    //         return <div
    //             key={i}
    //         ><DoubleCell origin_content={hunk.content}/><br/></div>
    //     } else if (hunk.option == "Destination_only") {
    //         return <div
    //             key={i}
    //         ><DoubleCell dest_content={hunk.content}/><br/></div>
    //     } else if (hunk.option == "Both") {
    //         if (!hunk.subDiffHunks) {
    //             return <div
    //                 key={i}
    //             ><DoubleCell origin_content={hunk.content} dest_content={hunk.content}/><br/></div>
    //         } else {
    //             let origin = ""
    //             let destination = ""
    //             hunk.subDiffHunks.map((subhunk) => {
    //                 if (subhunk.option == "Origin_only") {
    //                     origin += subhunk.content + "\n"
    //                 } else if (subhunk.option == "Destination_only") {
    //                     destination += subhunk.content + "\n"
    //                 } else if (subhunk.option == "Both") {
    //                     origin += subhunk.content + "\n"
    //                     destination += subhunk.content + "\n"
    //                 }
    //             });
    //             return <div
    //                 key={i}
    //             ><DoubleCell origin_content={origin} dest_content={destination}/><br/></div>
    //         }
    //     }
    // });
    let result = props!.DiffCommitDetail?.notebookCellDiffHunks.map((hunk, i) => {
        return <div
            key={i}
        ><SingleDiffCell diffHunk={hunk}/><br/></div>
    });
    return (
        <div>
            {result}
        </div>
    );
}

export default NotebookFileDiffPanel;
