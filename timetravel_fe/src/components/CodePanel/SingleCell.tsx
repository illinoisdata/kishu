import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "./Cell.css";
import {useEffect, useRef} from "react";


export interface SingleCellProps {
    execNumber?: string;
    content: string;
    cssClassNames?: string;
}

//helper functions
function countLines(text: string) {
    const lines = text.split("\n");
    return lines.length;
}

function SingleCell(props: SingleCellProps) {
    const aceRef = useRef<AceEditor | null>(null);
    // useEffect{
    //     () => {
    //         if(aceRef){
    //             aceRef.current?.editor.renderer.hideCursor()
    //         }
    //     }
    // }
    return (
        <div className="singleCellLayout">
      {!props.execNumber ? <span className="executionOrder">
          [&nbsp;&nbsp;]
      </span>: <span className="executionOrder">[{props.execNumber}]</span>}
            <AceEditor
                ref = {aceRef}
                className={"cell-code"}
                // className={!props.execNumber ? "code unexcecuted" : "code executed"}
                placeholder="Placeholder Text"
                mode="python"
                theme="github"
                name="blah2"
                fontSize={14}
                width="90%"
                height={(countLines(props.content) * 20).toString() + "px"}
                // height="10px"
                showPrintMargin={false}
                showGutter={false}
                highlightActiveLine={false}
                value={props.content}
                readOnly
                setOptions={{
                    enableBasicAutocompletion: false,
                    enableLiveAutocompletion: false,
                    enableSnippets: false,
                    showLineNumbers: true,
                    useWorker: false,
                    tabSize: 2,
                    dragEnabled: false
                }}
            />
        </div>
    );
}

export default SingleCell;
