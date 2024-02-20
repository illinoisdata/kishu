import "./index.css";
import {DiffVarHunk} from "../../util/DiffHunk";
import {Variable} from "../../util/Variable";
import {VariableRow} from "./VariableRow";
import {VersionChange} from "../../util/VariableVersionCompare";
import {PlusOutlined} from "@ant-design/icons";
import {Button} from "antd";
import {useState} from "react";

export interface VariablePanelProps {
    variables: Variable[] | DiffVarHunk[];
    diffMode: boolean;
}

const getRowClassName = (option: number) => {
    if(option === VersionChange.origin_only){
        return "origin-only-row"}
    if(option === VersionChange.destination_only){
        return "destination-only-row"}
    return ""
}

const findVariable = (_variables: Variable[]|DiffVarHunk[], queryVarNames: string, diffMode:boolean): Variable[]|DiffVarHunk[] => {
    if(diffMode){
        let variables = _variables as DiffVarHunk[]
        variables = variables.filter((variable) => {
            return queryVarNames === variable.content.variableName
        })
        return variables
    }
    else{
        let variables = _variables as Variable[]
        variables = variables.filter((variable) => {
            return queryVarNames === variable.variableName
        })
        return variables
    }
}

export function VariablePanel(props: VariablePanelProps) {
    const [input, setInput] = useState("")
    const [queryVarName, setQueryVarName] = useState("")
    const [watchVarNames, setWatchVarNames] = useState<string[]>([])
    let queryVarRows:any[] = []
    let watchVarRows:any[] = []
    let varRows = []
    const queryVars = findVariable(props.variables, queryVarName, props.diffMode)
    const watchedVars = watchVarNames.map((watchVarName) => {return findVariable(props.variables, watchVarName, props.diffMode)})

    const removeWatchedVariable = (idx:number) => {
        setWatchVarNames(watchVarNames.filter((_,i) => i !== idx))
    }

    // create the rows to display for all variables for the selected commit/diff commits
    varRows = props.variables.map((variable) => {
        return <VariableRow variable={props.diffMode?(variable as DiffVarHunk).content:(variable as Variable)} level={0}
                            className={props.diffMode?getRowClassName((variable as DiffVarHunk).option):undefined} iconName={"pic-center"}/>
    })

    // create the rows to display for the queried variable
    if(queryVarName !== ""){
        if(queryVars.length === 0) {
            //if the queried variable is not found, display an error message
            queryVarRows = [<VariableRow variable={{
                key:queryVarName,
                variableName:queryVarName,
                state: "not found",
                type: "name error",
                size: undefined,
                html: undefined,
            } as Variable} level={0} iconName={"alert"} result={true}/>]
        }
        else{
            //if the queried variable is found, display the variable
            queryVarRows = queryVars.map((variable) => {
                return <VariableRow variable={props.diffMode?(variable as DiffVarHunk).content:(variable as Variable)} level={0}
                                    className={props.diffMode?getRowClassName((variable as DiffVarHunk).option):undefined} iconName={"query-result"} result={true}/>
            })
        }
    }

    //create the rows to display for the watched variables
    if(watchVarNames.length > 0){
        watchVarRows = watchedVars.map((vars,idx) => {
            if(vars.length === 0) {
                //if the watch variable is not found, display an error variable
                queryVarRows.push(<VariableRow variable={{
                    key:watchVarNames[idx],
                    variableName:watchVarNames[idx],
                    state: "not found",
                    type: "name error",
                    size: undefined,
                    html: undefined,
                } as Variable} level={0} iconName={"alert"} removeWatchedVariable={() => removeWatchedVariable(idx)}/>)
            }
            else{
                //if the watch variable is found, display the variable
                return vars.map((variable) => {
                    return <VariableRow variable={props.diffMode?(variable as DiffVarHunk).content:(variable as Variable)} level={0}
                                        className={props.diffMode?getRowClassName((variable as DiffVarHunk).option):undefined} iconName={"monitor"} removeWatchedVariable={() => removeWatchedVariable(idx)}/>
                })
            }
        })
    }

    function handleKeyDown(event:any) {
        if (event.key === 'Enter') {
            setQueryVarName(input)
        }
    }
    function handleAddWatch() {
        setWatchVarNames([input,...watchVarNames])
        setQueryVarName("")
    }
    function handleInput(event:any) {
        setInput(event.target.value)
    }
    return(<div style={{marginLeft:40}}>
        <div className={"add-watch"}>
            <input className={"add-watch-input"} placeholder={"Add a watch to the variable you want to inspect (⏎)"}
            onKeyDown={handleKeyDown} onChange={handleInput}/>
            <PlusOutlined onClick={handleAddWatch} style={{paddingRight:10}}/>
        </div>
        {queryVarRows}
        {watchVarRows}
        {varRows}
    </div>)
}
