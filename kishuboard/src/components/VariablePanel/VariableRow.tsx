import { Variable } from "../../util/Variable";
import {useState} from "react";
import {CloseOutlined, DownOutlined, RightOutlined, PicCenterOutlined,ExclamationCircleOutlined,CarryOutOutlined,PushpinOutlined} from "@ant-design/icons";
import "./index.css";
import {yellow} from "@ant-design/colors";
import {DetailModal} from "./DetailModal";

type IconName = "pic-center" | "alert"|"query-result"|"monitor";

const COMPONENT_MAP: { [key in IconName]: React.ComponentType<any> } = {
    "pic-center": PicCenterOutlined,
    "alert":ExclamationCircleOutlined,
    "query-result":CarryOutOutlined,
    "monitor":PushpinOutlined
}
export interface VariableRowProps {
    variable: Variable
    level: number
    className?: string
    iconName: IconName
    removeWatchedVariable?: any
    result?:boolean
}

export function VariableRow(props: VariableRowProps):JSX.Element{
    const [fold, setFold] = useState(true);
    // const fold = true
    // const setFold = (value: boolean) => {}
    const Icon = COMPONENT_MAP[props.iconName]
    const [showDetailModal, setShowDetailModal] = useState(false)

    //use the color of variable name to distinguish the variable type (watched, queried, etc.)
    let color:string = "blue"
    if (props.iconName === "pic-center"){
        //normal variables
        color = "darkblue"
    }else if (props.iconName === "alert"){
        //queried variables
        color = "darkorange"
    }else if (props.iconName === "query-result"){
        color = "darkgreen"
    }else if (props.iconName === "monitor"){
        color = "darkred"
    }

    let showDetailButton: boolean = false

    if(props.variable.html || props.variable.state.includes("\\n")){
        showDetailButton = true
    }

    const parentVariableRow = (
        <div className={"parent-var-row"}>
            <span style={{color:color}}>{props.result?"result":props.variable.variableName}</span>
            <span> = </span>
            <span style={{color:"darkgray"}}> {"{" + props.variable.type + (props.variable.size?":" + props.variable.size:"") + "}"} </span>
            <span> {props.variable.state} </span>
        </div>
    )
    const childrenVariableRows = props.variable.children?.map((variable,index) => {
        return <VariableRow key={variable.variableName + index} variable={variable} level={props.level + 1} iconName={props.iconName}/>
    })
    return(
        <>
            <div className={`variable-row ${props.className}`} style={{marginLeft: 2 + 20 * props.level}} >
                {props.removeWatchedVariable?<CloseOutlined onClick={props.removeWatchedVariable}/>:undefined}
                {childrenVariableRows?(fold?<RightOutlined onClick={() => setFold(false)}/>:<DownOutlined onClick={() => setFold(true)}/>):undefined}
                <Icon style={{marginLeft:10,marginRight:4,color:yellow[7]}}/>
                {parentVariableRow}
                {showDetailButton?<span style={{marginLeft:10,marginRight:4,color:yellow[7],cursor:"pointer"}} onClick={() => setShowDetailModal(true)}>view detail</span>:undefined}
            </div>
            {childrenVariableRows&&!fold?childrenVariableRows:undefined}
            {showDetailModal && <DetailModal isOpen={showDetailModal} setIsModalOpen={setShowDetailModal} value={props. variable.state} html={props.variable.html} variableName={props.variable.variableName}/>}
        </>
    )
}