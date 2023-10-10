/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-18 14:27:43
 * @LastEditTime: 2023-08-01 08:52:32
 * @FilePath: /src/components/VariablePanel/ExecutedCodePanel.tsx
 * @Description:
 */

import "./index.css";
import { SearchOutlined } from "@ant-design/icons";
import Highlighter from "react-highlight-words";
import { Button, Input } from "antd";
import type { ColumnType, ColumnsType } from "antd/es/table";
import type { FilterConfirmProps } from "antd/es/table/interface";
import { Variable } from "../../util/Variable";
import React, { useRef, useState } from "react";
import { InputRef, Space, Switch, Table } from "antd";
import type { TableRowSelection } from "antd/es/table/interface";
import { DetailModal } from "./DetailModal";
import "./index.css";

export interface VariablePanelProps {
  variables: Variable[];
}

type DataIndex = keyof Variable;

export default function VariablePanel(props: VariablePanelProps) {
  const [detailVariableValue, setDetailVariableValue] = useState<
    string | undefined
  >(undefined);
  const [openModal, setOpenModal] = useState(false);
  function handleDetailClick(text: string) {
    setDetailVariableValue(text.replaceAll("\\n", "\n"));
    setOpenModal(true);
  }

  const [searchText, setSearchText] = useState("");
  const [searchedColumn, setSearchedColumn] = useState("");
  const searchInput = useRef<InputRef>(null);

  const handleSearch = (
    selectedKeys: string[],
    confirm: (param?: FilterConfirmProps) => void,
    dataIndex: DataIndex,
  ) => {
    confirm();
    setSearchText(selectedKeys[0]);
    setSearchedColumn(dataIndex);
  };

  const handleReset = (clearFilters: () => void) => {
    clearFilters();
    setSearchText("");
  };

  const getColumnSearchProps = (
    dataIndex: DataIndex,
  ): ColumnType<Variable> => ({
    filterDropdown: ({
      setSelectedKeys,
      selectedKeys,
      confirm,
      clearFilters,
      close,
    }) => (
      <div style={{ padding: 8 }} onKeyDown={(e) => e.stopPropagation()}>
        <Input
          ref={searchInput}
          placeholder={`Search ${dataIndex}`}
          value={selectedKeys[0]}
          onChange={(e) =>
            setSelectedKeys(e.target.value ? [e.target.value] : [])
          }
          onPressEnter={() =>
            handleSearch(selectedKeys as string[], confirm, dataIndex)
          }
          style={{ marginBottom: 8, display: "block" }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() =>
              handleSearch(selectedKeys as string[], confirm, dataIndex)
            }
            icon={<SearchOutlined />}
            size="small"
            style={{ width: 90 }}
          >
            Search
          </Button>
          <Button
            onClick={() => clearFilters && handleReset(clearFilters)}
            size="small"
            style={{ width: 90 }}
          >
            Reset
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => {
              confirm({ closeDropdown: false });
              setSearchText((selectedKeys as string[])[0]);
              setSearchedColumn(dataIndex);
            }}
          >
            Filter
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => {
              close();
            }}
          >
            close
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <SearchOutlined style={{ color: filtered ? "#1677ff" : undefined }} />
    ),
    onFilter: (value, record) =>
      record[dataIndex]!.toString()
        .toLowerCase()
        .includes((value as string).toLowerCase()),
    onFilterDropdownOpenChange: (visible) => {
      if (visible) {
        setTimeout(() => searchInput.current?.select(), 100);
      }
    },
    render: (text) =>
      searchedColumn === dataIndex ? (
        <Highlighter
          highlightStyle={{ backgroundColor: "#ffc069", padding: 0 }}
          searchWords={[searchText]}
          autoEscape
          textToHighlight={text ? text.toString() : ""}
        />
      ) : (
        text
      ),
  });

  const columns: ColumnsType<Variable> = [
    {
      title: "Name",
      width: "30%",
      dataIndex: "variableName",
      key: "variableName",
      ...getColumnSearchProps("variableName"),
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
