/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-18 14:27:43
 * @LastEditTime: 2023-08-01 08:52:32
 * @FilePath: /src/components/VariablePanel/index.tsx
 * @Description:
 */
import { Variable } from "../../util/Variable";
import React, { useState } from "react";
import { Space, Switch, Table } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { TableRowSelection } from "antd/es/table/interface";
import { DetailModal } from "./DetailModal";
import "./index.css";
export interface VariablePanelProps {
  variables: Variable[];
}

export default function VariablePanel(props: VariablePanelProps) {
  const [detailVariableValue, setDetailVariableValue] = useState<
    string | undefined
  >(undefined);
  const [openModal, setOpenModal] = useState(false);
  function handleDetailClick(text: string) {
    setDetailVariableValue(text.replaceAll("\\n", "\n"));
    setOpenModal(true);
  }

  const columns: ColumnsType<Variable> = [
    {
      title: "Name",
      dataIndex: "variableName",
      key: "variableName",
    },
    {
      title: "Type",
      dataIndex: "type",
      key: "type",
      // width: '12%',
    },
    {
      title: "Size",
      dataIndex: "size",
      // width: '30%',
      key: "size",
    },
    {
      title: "Value",
      dataIndex: "state",
      width: "30%",
      key: "state",
      // onCell: () => {
      //   return {
      //     style: {
      //       maxWidth: 100,
      //       overflow: "hidden",
      //       whiteSpace: "nowrap",
      //       textOverflow: "ellipsis",
      //       cursor: "pointer",
      //     },
      //   };
      // },
      ellipsis: true,
      render: (text) =>
        (text as string).includes("\\n") ? (
          <div className="custom-div" onClick={() => handleDetailClick(text)}>
            {text}
          </div>
        ) : (
          text
        ),
    },
  ];
  return (
    <>
      <Table columns={columns} dataSource={props.variables} />
      <DetailModal
        value={detailVariableValue}
        isOpen={openModal}
        setIsModalOpen={setOpenModal}
      ></DetailModal>
    </>
  );
}
