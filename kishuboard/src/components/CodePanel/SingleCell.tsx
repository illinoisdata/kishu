import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "./Cell.css";
import {useEffect, useRef} from "react";
import Markdown from 'react-markdown'
import {FONTSIZE} from "../HistoryPanel/GraphConsts";


export interface SingleCellProps {
    execNumber?: string;
    content: string;
    cssClassNames?: string;
    isMarkdown?: boolean;
}

//helper functions
function countLines(text: string) {
    const lines = text.split("\n");
    return lines.length;
}

function SingleCell(props: SingleCellProps) {
    const aceRef = useRef<AceEditor | null>(null);
    let singleCell: JSX.Element = <> </>;
    if(props.isMarkdown){
        singleCell = (
            <div className="singleCellLayout" style={{marginLeft:40}}>
                {/*{!props.execNumber ? <span className="executionOrder">*/}
                {/*    [&nbsp;&nbsp;]:*/}
                {/*</span>: <span className="executionOrder">[{props.execNumber}]: </span>}*/}
                <Markdown
                    className={"cell-code type_markdown"}
                >
                    {props.content}
                </Markdown>
            </div>
        )

    }else{
        singleCell = (
            <div className="singleCellLayout">
                {!props.execNumber ? <div className="executionOrder">
          [&nbsp;&nbsp;]:
      </div>: <div className="executionOrder">[{props.execNumber}]: </div>}
                <AceEditor
                    ref = {aceRef}
                    className={"cell-code markdown"}
                    // className={!props.execNumber ? "code unexcecuted" : "code executed"}
                    placeholder="Placeholder Text"
                    mode="python"
                    theme="github"
                    name="blah2"
                    fontSize={14}
                    width="90%"
                    height={(((countLines(props.content)) + 1) * (FONTSIZE + 3.5)).toString() + "px"}
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
        )
    }
    return (
     singleCell
    );
}

export default SingleCell;
