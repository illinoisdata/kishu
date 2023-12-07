import {useContext} from "react";
import {AppContext} from "../../App";
import SingleDiffCell from "./SingleDiffCell";


function NotebookFileDiffPanel() {
    const props = useContext(AppContext);

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
