/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 11:38:34
 * @LastEditTime: 2023-07-29 13:29:52
 * @FilePath: /src/components/CodePanel/SingleCell.tsx
 * @Description:
 */
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "./Cell.css";
import {ReactNode} from "react";
import {diff as DiffEditor} from "react-ace";
import "./DoubleCell.css"

export interface DoubleCellProps {
    origin_content?: string,
    dest_content?: string,
    cssClassNames?: string;
}

//helper functions
function countLines(text: string) {
    const lines = text.split("\n");
    return lines.length;
}

function DoubleCell(props: DoubleCellProps) {
    let result: ReactNode
    if (props.dest_content && props.origin_content) {
        result = <DiffEditor
            className={"codeMarker"}
            value={[props.origin_content, props.dest_content]}
            height={(Math.max(countLines(props.origin_content), countLines(props.dest_content)) * 30).toString() + "px"}
            width={"100%"}
            mode="text"


        />
    } else if (props.origin_content) {
        result = <DiffEditor
            className={"codeMarker"}
            value={[props.origin_content, ""]}
            height={(countLines(props.origin_content) * 30).toString() + "px"}
            width={"100%"}
            mode="text"

        />
    } else if (props.dest_content) {
        result = <DiffEditor
            className={"codeMarker"}
            value={["", props.dest_content]}
            height={(countLines(props.dest_content) * 30).toString() + "px"}
            width={"100%"}
            mode="text"

        />
    } else {
        result = <div></div>
    }
    return result
    // return   <DiffEditor
    //     value={["Test code differences\n a= b", "Test code difference\n a= b"]}
    //     height="1000px"
    //     width="1000px"
    //     className={"codeMarker"}
    // />
}

export default DoubleCell;
