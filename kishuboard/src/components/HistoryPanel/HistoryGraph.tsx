// input PointRenderer[], return an SVG
import {PointRenderInfo} from "../../util/PointRenderInfo";
import {VisPoint, VisPointType} from "../../util/VisPoint";
import {COMMITHEIGHT, COMMITRADIUS, GRAPHFONTSIZE, MARGINMESSAGE, MESSAGEMARGINX} from "./GraphConsts";
import React from "react";
import "./historyPanel.css";
import "./Info.css";

export interface HistoryGraphProps {
    pointRendererInfos: Map<string, PointRenderInfo>;
    visPoints: Map<string, {point:VisPoint,idx:number}>;
    currentVarID: string | undefined;
    currentCodeID: string | undefined;
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

    function getSVGLine(pointRenderInfo:[string,PointRenderInfo],pID:string, dashLine:boolean,strokeWidth?:number, color?:string){
        let me = props.visPoints.get(pointRenderInfo[0]);
        let parent = props.visPoints.get(pID);
        let parentCX = props.pointRendererInfos.get(pID!)?.cx;
        let parentCY = props.pointRendererInfos.get(pID!)?.cy;
        // let dashLine = me?.point.type===VisPointType.GROUP_FOLD?false:parent?.point.commit.variableVersion === me?.point.commit.variableVersion;
        //if has parent and parent is not folded in the same date.
        if (parentCX && parentCY && (parentCY !== pointRenderInfo[1].cy)) {
            return (
                <path
                    strokeDasharray={dashLine ? "7,3" : ""}
                    stroke={color?color:pointRenderInfo[1].color}
                    strokeWidth={strokeWidth?strokeWidth:1}
                    fill={"none"}
                    d={`M ${parentCX} ${parentCY - COMMITHEIGHT / 2 + GRAPHFONTSIZE / 2 + MARGINMESSAGE} L ${pointRenderInfo[1].cx} ${
                        (parentCY- COMMITHEIGHT / 2 + GRAPHFONTSIZE / 2 + MARGINMESSAGE) - COMMITHEIGHT / 2
                    } L ${pointRenderInfo[1].cx} ${pointRenderInfo[1].cy - COMMITHEIGHT / 2 + GRAPHFONTSIZE / 2 + MARGINMESSAGE}`}
                />
            );
        }
        return <></>;
    }

    function getStateLabel(content:string, x:number, y:number, width:number, bgColor:string, txtColor:string, borderColor?:string){
        return <>
        <rect
            x={x - 3}
            y={y - GRAPHFONTSIZE - 2}
            width={width}
            height={GRAPHFONTSIZE + 3}
            fill={bgColor}
            stroke={borderColor?borderColor:""}
        >
        </rect>
        <text
            x={x}
            y={y - 3}
            fill = {txtColor}
            fontSize={GRAPHFONTSIZE}
        >
            {content}
        </text>

    </>
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
                let varParentLine =  getSVGLine(pointRenderInfo,parentID,false);
                let nbParentLine = <></>
                let nbPNotation = <></>
                let varPNotation = <></>
                if(me!.point.nbParentID != me!.point.parentID){
                    nbParentLine = getSVGLine(pointRenderInfo,me!.point.nbParentID,true,2,props.pointRendererInfos.get(me!.point.nbParentID)!.color);
                    // if(me?.point.commit.oid === props.selectedPointID){
                    //     varParentLine = getSVGLine(pointRenderInfo,me!.point.parentID,false,2.5,props.pointRendererInfos.get(parentID)?.color);
                    //     nbParentLine = getSVGLine(pointRenderInfo,me!.point.nbParentID,true,2.8,props.pointRendererInfos.get(me!.point.nbParentID)!.color);
                    //     nbPNotation = getStateLabel("code parent",props.pointRendererInfos.get(me!.point.nbParentID)!.cx - COMMITRADIUS + MESSAGEMARGINX, props.pointRendererInfos.get(me!.point.nbParentID)!.cy + COMMITHEIGHT / 2 - 10, 90,"none",COLCODELABEL,COLCODELABEL)
                    //     varPNotation = getStateLabel("variable parent",props.pointRendererInfos.get(me!.point.parentID)!.cx - COMMITRADIUS + MESSAGEMARGINX, props.pointRendererInfos.get(me!.point.parentID)!.cy + COMMITHEIGHT / 2 - 10, 115,"none",COLVARLABEL,COLVARLABEL)
                    // }else{
                    //     nbParentLine = getSVGLine(pointRenderInfo,me!.point.nbParentID,true,1.4);
                    // }
                }
                return(
                    <>
                        {varParentLine}
                        {nbParentLine}
                        {/*{nbPNotation}*/}
                        {/*{varPNotation}*/}
                    </>
                );
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
                    radius = COMMITRADIUS;}
                const x1 = info.cx - radius; // Left
                const x2 = info.cx + radius; // Right
                const y1 = info.cy - COMMITHEIGHT / 2 + GRAPHFONTSIZE / 2 +radius/2 + MARGINMESSAGE; // Horizontal line y-coordinate
                const y2 = info.cy - COMMITHEIGHT / 2 + GRAPHFONTSIZE / 2 - radius / 2 + MARGINMESSAGE; // Top
                const y3 = info.cy - COMMITHEIGHT / 2 + GRAPHFONTSIZE / 2 +(3 * radius) / 2 + MARGINMESSAGE
                return (
                    <>
                    <rect
                        pointerEvents={"visible"}
                        x={info.cx - radius}
                        y={info.cy - COMMITHEIGHT / 2 + GRAPHFONTSIZE / 2 - radius / 2 + MARGINMESSAGE}
                        width={point.type === VisPointType.GROUP_FOLD?2 * (radius):2 * COMMITRADIUS}
                        height={point.type === VisPointType.GROUP_FOLD?2 * (radius):2 * COMMITRADIUS}
                        fill={point.type === VisPointType.GROUP_FOLD || point.type === VisPointType.GROUP_UNFOLE?"none":info.color}
                        stroke={point.parentID == point.nbParentID?info.color:props.pointRendererInfos.get(point.nbParentID)!.color}
                        strokeWidth={point.parentID == point.nbParentID?1:2}
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
                        y={info.cy - COMMITHEIGHT / 2 + GRAPHFONTSIZE + MARGINMESSAGE}
                        fontWeight={id == props.selectedPointID ? "bold" : "normal"}
                        fontSize={GRAPHFONTSIZE}
                    >
                        {props.visPoints.get(id)?.point.commit.message}
                    </text>
                    {id == props.currentVarID &&
                        <>
                            {getStateLabel("HEAD: Variable",info.cx - COMMITRADIUS + MESSAGEMARGINX,info.cy + COMMITHEIGHT / 2 - MARGINMESSAGE, 108,info.color,"white")}
                        </>
                    }
                    {id == props.currentCodeID &&
                        <>
                            {getStateLabel("HEAD: Code",id == props.currentVarID?info.cx - COMMITRADIUS + MESSAGEMARGINX + 120:info.cx - COMMITRADIUS + MESSAGEMARGINX,info.cy + COMMITHEIGHT / 2 - MARGINMESSAGE, 86,"none",info.color,info.color)}
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
