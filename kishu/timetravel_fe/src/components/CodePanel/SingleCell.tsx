/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 11:38:34
 * @LastEditTime: 2023-07-18 14:22:55
 * @FilePath: /src/components/CodePanel/SingleCell.tsx
 * @Description:
 */
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "./SingleCell.css";
export interface SingleCellProps {
  execNumber: number;
  oid: number;
  content: string;
}
//helper functions
function countLines(text: string) {
  const lines = text.split("\n");
  return lines.length;
}

function SingleCell(props: SingleCellProps) {
  return (
    <div className="singleCellLayout">
      <span className="executionOrder">
        &#91;{props.execNumber === -1 ? "" : props.execNumber}&#93;
      </span>
      <AceEditor
        className={
          props.execNumber === -1 ? "code unexcecuted" : "code success"
        }
        placeholder="Placeholder Text"
        mode="python"
        theme="github"
        name="blah2"
        fontSize={14}
        width="100%"
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
