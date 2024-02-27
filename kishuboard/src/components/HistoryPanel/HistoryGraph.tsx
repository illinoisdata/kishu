// input PointRenderer[], return an SVG
import {PointRenderInfo} from "../../util/PointRenderInfo";
import {VisPoint, VisPointType} from "../../util/VisPoint";
import {COMMITHEIGHT, COMMITRADIUS, FONTSIZE, MESSAGEMARGINX} from "./GraphConsts";
import React from "react";
import "./historyPanel.css";
import "./Info.css";

export interface HistoryGraphProps {
    pointRendererInfos: Map<string, PointRenderInfo>;
    visPoints: Map<string, {point:VisPoint,idx:number}>;
    currentPointID: string | undefined;
    svgMaxX: number;
    svgMaxY: number;
    selectedPointID: string | undefined;
    svgMessagePosition: number[];
    setUnfoldedGroup: any;
    unfoldedGroup: number[]|undefined;
}


function _HistoryGraph(props: HistoryGraphProps) {
    const unfoldGroup = (groupID: number) => {
        if(!props.unfoldedGroup){
            props.setUnfoldedGroup([groupID]);
        }else{
            props.setUnfoldedGroup([...props.unfoldedGroup, groupID])
        }
    }

    const foldGroup = (groupID: number) => {
        if(props.unfoldedGroup){
            props.setUnfoldedGroup(props.unfoldedGroup.filter((id) => id !== groupID))
        }
    }
    return (
        <svg
            overflow={"visible"}
            style={{zIndex: 2, marginLeft: 8}}
            width={props.svgMaxX}
            height={props.svgMaxY}
        >
            {Array.from(props.pointRendererInfos).map((pointRenderInfo) => {
                let me = props.visPoints.get(pointRenderInfo[0]);
                let parentID = me!.point.parentID;
                let parent = props.visPoints.get(parentID);
                let parentCX = props.pointRendererInfos.get(parentID!)?.cx;
                let parentCY = props.pointRendererInfos.get(parentID!)?.cy;
                let dashLine = me?.point.type===VisPointType.GROUP_FOLD?false:parent?.point.commit.variableVersion === me?.point.commit.variableVersion;
                if (parentCX && parentCY && (parentCY !== pointRenderInfo[1].cy)) {
                    return (
                        <path
                            strokeDasharray={dashLine ? "3,3" : ""}
                            stroke={pointRenderInfo[1].color}
                            fill={"none"}
                            d={`M ${parentCX} ${parentCY - COMMITHEIGHT / 2 + FONTSIZE / 2} L ${pointRenderInfo[1].cx} ${
                                (parentCY- COMMITHEIGHT / 2 + FONTSIZE / 2) - COMMITHEIGHT / 2
                            } L ${pointRenderInfo[1].cx} ${pointRenderInfo[1].cy - COMMITHEIGHT / 2 + FONTSIZE / 2}`}
                        />
                    );
                }
                return <></>;
            })}
            {Array.from(props.pointRendererInfos).map((pointRenderInfo) => {
                // find commit index according to commitID
                let idx = props.visPoints.get(pointRenderInfo[0])?.idx;
                let info = pointRenderInfo[1];
                let id = pointRenderInfo[0];
                let point = props.visPoints.get(id)!.point;
                if(info.folded){
                    return <></>
                }

                // Calculate the coordinates of the plus icon
                let radius = COMMITRADIUS;
                if(point.type === VisPointType.GROUP_FOLD){
                    radius = COMMITRADIUS + 1;}
                const x1 = info.cx - radius; // Left
                const x2 = info.cx + radius; // Right
                const y1 = info.cy - COMMITHEIGHT / 2 + FONTSIZE / 2 +radius/2 ; // Horizontal line y-coordinate
                const y2 = info.cy - COMMITHEIGHT / 2 + FONTSIZE / 2 - radius / 2; // Top
                const y3 = info.cy - COMMITHEIGHT / 2 + FONTSIZE / 2 +(3 * radius) / 2
                // const y3 = info.cy - COMMITHEIGHT / 2 + FONTSIZE / 2  + COMMITRADIUS + 10; // Bottom
                // (info.cx,y); (info.cx,y + radius)
                // (info.cx - radius,y + 1/2 * radius); (info.cx + radius, y + 1/2 radius)
                return (
                    <>
                    <rect
                        pointerEvents={"visible"}
                        x={info.cx - radius}
                        y={info.cy - COMMITHEIGHT / 2 + FONTSIZE / 2 - radius / 2}
                        width={point.type === VisPointType.GROUP_FOLD?2 * (radius):2 * COMMITRADIUS}
                        height={point.type === VisPointType.GROUP_FOLD?2 * (radius):2 * COMMITRADIUS}
                        fill={point.type === VisPointType.GROUP_FOLD || point.type === VisPointType.GROUP_UNFOLE?"none":info.color}
                        stroke={info.color}
                        onClick={() => {
                            if(point.type === VisPointType.GROUP_FOLD){
                                unfoldGroup(point.groupID)
                            }else if(point.type === VisPointType.GROUP_UNFOLE){
                                foldGroup(point.groupID)
                            }
                        }}
                    />
                        {point.type === VisPointType.GROUP_FOLD &&
                            <g id="plusIcon" stroke = {info.color} strokeWidth="2" onClick={() => {
                                if(point.type === VisPointType.GROUP_FOLD){
                                    unfoldGroup(point.groupID)
                                }else if(point.type === VisPointType.GROUP_UNFOLE){
                                    foldGroup(point.groupID)
                                }
                            }}>
                                <line x1={x1} y1={y1} x2={x2} y2={y1} />
                                <line x1={(x1 + x2)/2} y1={y2} x2={(x1 + x2)/2} y2={y3} />
                            </g>
                        }


                    <text
                        x={props.svgMessagePosition[idx!] - COMMITRADIUS + MESSAGEMARGINX}
                        y={info.cy - COMMITHEIGHT / 2 + FONTSIZE}
                        fontWeight={id == props.selectedPointID ? "bold" : "normal"}
                    >
                        {props.visPoints.get(id)?.point.commit.message}
                    </text>
                    {id == props.currentPointID &&
                        <>
                            <text
                                x={info.cx - COMMITRADIUS + MESSAGEMARGINX}
                                y={info.cy + COMMITHEIGHT / 2 - 10}
                                fill = "red"
                            >
                                current notebook state
                            </text>

                        </>

                    }
                    </>
                );
            })}

        </svg>
    );
}

//helper function
function darkerColorGenerator(color: string) {
    console.log(color)
    color = color.substring(1) // remove #
    let col = parseInt(color, 16); // convert to integer
    let num_color = ((col & 0x7E7E7E) >> 1) | (col & 0x808080)
    console.log(num_color)
    return "#" + num_color.toString(16);
}
export const HistoryGraph = React.memo(_HistoryGraph);
