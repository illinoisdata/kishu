import "./index.css";
import type {ColumnsType} from "antd/es/table";
import React, {useRef, useState} from "react";
import {InputRef, Table} from "antd";
import {DetailModal} from "./DetailModal";
import "./index.css";
import {getColumnSearchProps} from "./searchVariable";
import {DiffVarHunk} from "../../util/DiffHunk";
import {VersionChange} from "../../util/VariableVersionCompare";
import {GetTableRowDiff, GetTableRowNonDiff, TableRowDiff, TableRowNonDiff} from "./TableRow";
import {Variable} from "../../util/Variable";

export interface VariablePanelProps {
    variables: Variable[] | DiffVarHunk[];
    diffMode: boolean
}

// state and handle logic about detail modal
function useDetailModal() {
    const [openModal, setOpenModal] = useState(false);
    const [detailVariableHtml, setDetailVariableHtml] = useState<string | undefined>(undefined);
    const [detailVariableValue, setDetailVariableValue] = useState<string>("");

    function handleDetailClick(variableValue:string, html?:string) {
        setOpenModal(true);
        setDetailVariableHtml(html)
        setDetailVariableValue(variableValue)
    }

    return [openModal, setOpenModal, handleDetailClick, detailVariableHtml, detailVariableValue] as const;
}

// columns of the tables
function getTableColumns(handleDetailClick:(variableValue:string, html?:string) => void, setSearchText:any, searchText:string, setSearchedColumn: any, searchedColumn:string, searchInput:React.RefObject<InputRef>,) {
        const columns: ColumnsType<any> = [
            {
                title: "Variable Name",
                width: "30%",
                dataIndex: "variableName",
                key: "variableName",
                ...getColumnSearchProps("variableName",setSearchText, searchText, setSearchedColumn, searchedColumn, searchInput),
            },
            {
                title: "Type",
                dataIndex: "type",
                key: "type",
            },
            {
                title: "Size",
                dataIndex: "size",
                key: "size",
            },
            {
                title: "Value",
                dataIndex: "state",
                width: "30%",
                key: "state",
                ellipsis: true,
                render: (text,record) =>
                    (text as string).includes("\\n") ? (
                        <div className="multiline-table-value" onClick={() => handleDetailClick(text.replace("\\n","\n"),record.html)}>
                            {text}
                        </div>
                    ) : (
                        text
                    ),
            },
        ];
        return columns
}

export function VariablePanel(props: VariablePanelProps) {
    const [searchText, setSearchText] = useState("");
    const [searchedColumn, setSearchedColumn] = useState("");
    const searchInput = useRef<InputRef>(null);


    const [isDetailModalOpen, setOpenModal, handleDetailClick, detailVariableHtml, detailVariableValue] = useDetailModal();

    const getRowClassName = (record:TableRowDiff) => {
        if(record.option === VersionChange.origin_only){
            return "origin-only-row"}
        if(record.option === VersionChange.destination_only){
            return "destination-only-row"}
        return ""
    }

    let table:JSX.Element
    if(props.diffMode){
        const data = (props.variables as DiffVarHunk[]).map((hunk) => GetTableRowDiff(hunk.content, hunk.option))
        table = <Table columns={getTableColumns(handleDetailClick,setSearchText, searchText, setSearchedColumn, searchedColumn, searchInput) as ColumnsType<TableRowDiff>} dataSource={data} rowClassName={getRowClassName}/>
    }else{
        const data = (props.variables as Variable[]).map((variable) => GetTableRowNonDiff(variable))
        table = <Table columns={getTableColumns(handleDetailClick,setSearchText, searchText, setSearchedColumn, searchedColumn, searchInput) as ColumnsType<TableRowNonDiff>} dataSource={data}/>
    }

    return (
        <>
            {table}
            <DetailModal
                isOpen={isDetailModalOpen}
                setIsModalOpen={setOpenModal}
                html={detailVariableHtml}
                value={detailVariableValue}
            ></DetailModal>
        </>
    );
}
