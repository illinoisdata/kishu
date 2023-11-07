import "./TimeGroupHeader.css";
import "../utility.css"
export interface TimeGroupHeaderProps {
    header: string;
}
export function TimeGroupHeader(props: TimeGroupHeaderProps) {
    return (
        <div className={"timeGroupHeaderContainer"}>
             <div className={"u-same_row timeGroupHead"}>{props.header}</div>
        </div>
    );
}
