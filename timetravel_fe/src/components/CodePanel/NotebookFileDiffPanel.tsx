import {useContext} from "react";
import {AppContext} from "../../App";
import SingleDiffCell from "./SingleDiffCell";


export function NotebookFileDiffPanel() {
    const props = useContext(AppContext);

    let result = props!.diffCodeDetail?.notebookCellDiffHunks.map((hunk, i) => {
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
