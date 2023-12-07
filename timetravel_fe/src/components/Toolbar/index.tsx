import React from "react";
import "./toolbar.css";
import "../utility.css";
import {SearchOutlined} from "@ant-design/icons";
import {Button, Input, ConfigProvider, Checkbox} from "antd";
import DropdownBranch from "./DropDownBranch";
import {CheckboxChangeEvent} from "antd/es/checkbox";

export interface toolBarProps{
    setInDiffMode: any;
}

function _Toolbar(props: toolBarProps) {
    const onDiffModeChange = (e: CheckboxChangeEvent) => {
        props?.setInDiffMode(e.target.checked);
    };

    return (
        <>
            <ConfigProvider
                theme={{
                    "components": {
                        "Button": {
                            "colorPrimary": "rgb(219,222,225)",
                            "primaryColor": "rgb(87,89,90)"
                        },
                        "Input": {
                            "colorBgContainer": "rgb(219,222,225)",
                            "colorText": "rgb(87,89,90)",
                            "colorBgContainerDisabled": "rgb(219,222,225)",
                            "colorTextDisabled": "rgb(87,89,90)",
                            "colorTextPlaceholder": "rgb(87,89,90)"
                        },
                        "Select": {
                            "colorBgContainer": "rgb(219,222,225)",
                            "colorText": "rgb(87,89,90)",
                            "colorTextPlaceholder": "rgb(87,89,90)",
                            "optionSelectedBg": "rgb(197,202,207)"
                        },
                    }
                }}
            >
                {" "}
                <div className="toolBar">
                    <Input
                        placeholder={"Notebook Name: " + globalThis.NotebookID}
                        disabled={true}
                        style={{width: "20%"}}
                    />
                    <div className="searchBar">
                        <Input
                            placeholder="input search text"
                            // disabled={true}

                        />
                        <Button
                            type="primary" shape={"round"} icon={<SearchOutlined/>}
                        />
                    </div>

                    <Checkbox onChange={onDiffModeChange}>DiffMode</Checkbox>

                    <div>
                        <DropdownBranch/>
                    </div>

                    {/* onSearch={} */}
                </div>
            </ConfigProvider>
        </>
    );
}

export const Toolbar = React.memo(_Toolbar)
