import "./index.css";
import type {ColumnsType} from "antd/es/table";
import {Variable} from "../../util/Variable";
import React, {useRef, useState} from "react";
import {InputRef, Space, Table} from "antd";
import {DetailModal} from "./DetailModal";
import "./index.css";
import {getColumnSearchProps} from "./searchVariable";

export interface VariablePanelProps {
    variables: Variable[];
}

// state and handle logic about detail modal
function useDetailModal() {
    const [openModal, setOpenModal] = useState(false);
    const [detailVariableHtml, setDetailVariableHtml] = useState<string | undefined>(undefined);

    function handleDetailClick(html?:string) {
        setOpenModal(true);
        setDetailVariableHtml(html)
    }

    return [openModal, setOpenModal, handleDetailClick, detailVariableHtml] as const;
}

// columns of the tables
function getTableColumns(handleDetailClick:(html?:string) => void, setSearchText:any, searchText:string, setSearchedColumn: any, searchedColumn:string, searchInput:React.RefObject<InputRef>){
    const columns: ColumnsType<Variable> = [
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
                    <div className="multiline-table-value" onClick={() => handleDetailClick(record.html)}>
                        {text}
                    </div>
                ) : (
                    text
                ),
        },
    ];
    return columns
}

export default function VariablePanel(props: VariablePanelProps) {
    const [searchText, setSearchText] = useState("");
    const [searchedColumn, setSearchedColumn] = useState("");
    const searchInput = useRef<InputRef>(null);


    const [isDetailModalOpen, setOpenModal, handleDetailClick, detailVariableHtml] = useDetailModal();

    return (
        <>
            <Table columns={getTableColumns(handleDetailClick,setSearchText, searchText, setSearchedColumn, searchedColumn, searchInput)} dataSource={props.variables}/>
            <DetailModal
                isOpen={isDetailModalOpen}
                setIsModalOpen={setOpenModal}
                html={detailVariableHtml}
            ></DetailModal>
        </>
    );
}
