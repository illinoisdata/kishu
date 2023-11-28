// input PointRenderer[], return an SVG
import {PointRenderInfo} from "../../util/PointRenderInfo";
import {Commit} from "../../util/Commit";
import {COMMITHEIGHT, COMMITRADIUS, CURRENTCOMMITRADUIS, MESSAGEMARGINX, MESSAGEMARGINY} from "./GraphConsts";
import React from "react";
import "./historyPanel.css";

export interface HistoryGraphProps {
    pointRendererInfos: Map<string, PointRenderInfo>;
    Commits: Map<string, Commit>;
    currentCommitID: string;
    svgMaxX: number;
    svgMaxY: number;
}

function _HistoryGraph(props: HistoryGraphProps) {
    return (
        <svg
            overflow={"visible"}
            style={{zIndex: 2}}
            width={props.svgMaxX}
            height={props.svgMaxY}
        >
            {Array.from(props.pointRendererInfos).map((commitID_info) => {
                let me = props.Commits.get(commitID_info[0]);
                let parentOid = me!.parentOid;
                let parent = props.Commits.get(parentOid);
                let parentCX = props.pointRendererInfos.get(parentOid!)?.cx;
                let parentCY = props.pointRendererInfos.get(parentOid!)?.cy;
                let dashLine = parent?.variableVersion === me?.variableVersion;
                if (parentCX && parentCY) {
                    return (
                        <path
                            strokeDasharray={dashLine ? "3,3" : ""}
                            stroke={commitID_info[1].color}
                            fill={"none"}
                            d={`M ${parentCX} ${parentCY} L ${commitID_info[1].cx} ${
                                parentCY - COMMITHEIGHT / 2
                            } L ${commitID_info[1].cx} ${commitID_info[1].cy}`}
                        />
                    );
                }
                return <></>;
            })}
            {Array.from(props.pointRendererInfos.values()).map((info) => {
                if(info.folded){
                    return <></>
                }
                return (
                    <>
                    <rect
                        x={info.cx - COMMITRADIUS}
                        y={info.cy - COMMITRADIUS}
                        width={2 * COMMITRADIUS}
                        height={2 * COMMITRADIUS}
                        fill={info.color}
                        onClick={() => {
                        }}
                    />
                    <text
                        x={info.cx - COMMITRADIUS + MESSAGEMARGINX}
                        y={info.cy - COMMITRADIUS - MESSAGEMARGINY}>
                        try text
                    </text>
                    </>
                );
            })}

            <circle
                cx={props.pointRendererInfos.get(props!.currentCommitID!)?.cx}
                cy={props.pointRendererInfos.get(props!.currentCommitID!)?.cy}
                r={CURRENTCOMMITRADUIS}
                fill={"Red"}
            />
        </svg>
    );
}

export const HistoryGraph = React.memo(_HistoryGraph);
