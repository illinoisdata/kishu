/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 11:38:34
 * @LastEditTime: 2023-07-29 13:29:52
 * @FilePath: /src/components/CodePanel/SingleCell.tsx
 * @Description:
 */
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "./Cell.css";


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
    return (
        <div className="singleCellLayout">
      <span className="executionOrder left">
        &#91;{props.execNumber === "-1" ? " " : props.execNumber}&#93; :
      </span>
            <AceEditor
                className={props.cssClassNames ? props.cssClassNames : "notebook"}
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
                }}
            />
        </div>
    );
}

export default SingleCell;
