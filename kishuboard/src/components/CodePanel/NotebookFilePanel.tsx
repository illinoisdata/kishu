import {useContext,} from "react";
import SingleCell from "./SingleCell";
import {AppContext} from "../../App";


export function NotebookFilePanel() {
    const props = useContext(AppContext);
    return (
        <div>
            {props!.selectedCommit!.codes!.map((code, i) => (
                <div
                    key={i}
                >
                    <SingleCell execNumber={code.execNum} content={code.content} cssClassNames={"notebook"} isMarkdown={code.type === "markdown"}/>
                    <br/>
                </div>
            ))}
        </div>
    );
}

