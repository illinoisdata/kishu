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
import "./SingleCell.css";
import {useContext} from "react";
import {AppContext} from "../../App";

export interface SingleCellProps {
    execNumber?: string;
    content: string;
}

//helper functions
function countLines(text: string) {
    const lines = text.split("\n");
    return lines.length;
}

function SingleCell(props: SingleCellProps) {
    const props1 = useContext(AppContext);
    return (
        <div className="singleCellLayout">
      <span className="executionOrder left">
        &#91;{props.execNumber === "-1" ? " " : props.execNumber}&#93;
      </span>
            <AceEditor
                className={"code"}
                // className={!props.execNumber ? "code unexcecuted" : "code executed"}
                placeholder="Placeholder Text"
                mode="python"
                theme="github"
                name="blah2"
                fontSize={14}
                width="90%"
                height={(countLines(props.content) * 30).toString() + "px"}
                // height="10px"
                showPrintMargin={false}
                showGutter={true}
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
