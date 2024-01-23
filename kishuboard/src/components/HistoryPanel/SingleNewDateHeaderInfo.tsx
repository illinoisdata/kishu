import {DownOutlined, RightOutlined} from "@ant-design/icons";
import React from "react";
import "./Info.css";
import {formatDate} from "../../util/ExtractDateFromString";
export interface SingleNewDateHeaderProps {
    newDate: string;
    commitNumber:number;
    setIsDateFolded: any;
    isDateFolded?:Map<string,boolean>;
    y_position: number;
}

function _SingleNewDateHeader(props: SingleNewDateHeaderProps) {
    const isFolded = props.isDateFolded?.get(props.newDate)
    return (
        <div
            className={"new_date"}
            onClick={() => {
                if (isFolded) {
                    props.setIsDateFolded(new Map(props.isDateFolded?.set(props.newDate, false)));
                }
                else {
                    //fold the date
                    if(!props.isDateFolded) {
                        props.setIsDateFolded(new Map<string, boolean>().set(props.newDate, true));
                    }
                    else {
                        props.setIsDateFolded(new Map(props.isDateFolded?.set(props.newDate, true)));
                    }
                }
            }}
            style={{top: props.y_position}}
        >
            <span>{isFolded?<RightOutlined/>:<DownOutlined/>} {formatDate(props.newDate)}</span> {isFolded?props.commitNumber + " commits collapsed":""}
        </div>
    );
}

export const SingleNewDateHeaderInfo = React.memo(_SingleNewDateHeader);