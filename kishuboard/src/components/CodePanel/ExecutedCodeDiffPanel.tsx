import {useContext} from "react";
import {AppContext} from "../../App";
import SingleDiffCell from "./SingleDiffCell"
import "./Cell.css"


export function ExecutedCodeDiffPanel() {
    const props = useContext(AppContext);
    return (
        <div className="executed-code">
            {props!.diffCodeDetail?.executedCellDiffHunks.map((hunk, i) => {
                return <div
                    key={i}
                ><SingleDiffCell diffHunk={hunk}/><br/></div>
            })}
        </div>
    )
}
