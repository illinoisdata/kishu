/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 11:38:34
 * @LastEditTime: 2023-07-14 14:38:45
 * @FilePath: /src/components/CodePanel/SingleCell.tsx
 * @Description:
 */
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "./SingleCell.css";
function SingleCell() {
  return (
    <div className="singleCellLayout">
      <div className="executionOrder">[1]</div>
      <AceEditor
        placeholder="Placeholder Text"
        mode="python"
        theme="github"
        name="blah2"
        fontSize={14}
        width="100%"
        height="300 ptx"
        showPrintMargin={true}
        showGutter={true}
        highlightActiveLine={true}
        value={`a=1`}
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
