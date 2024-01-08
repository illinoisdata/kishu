import {useContext} from "react";
import {AppContext} from "../../App";
import SingleDiffCell from "./SingleDiffCell";


export function ExecutedCodeDiffPanel() {
    const props = useContext(AppContext);
    return (
        <div>
            {props!.diffCodeDetail?.executedCellDiffHunks.map((hunk, i) => {
                return <div
                    key={i}
                ><SingleDiffCell diffHunk={hunk}/><br/></div>
            })}
        </div>
    )
}
