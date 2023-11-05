/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 10:20:09
 * @LastEditTime: 2023-07-15 22:18:28
 * @FilePath: /src/components/Toolbar/ExecutedCodePanel.tsx
 * @Description: toolBar includes rollback buttons, and the menu to choose rollback type.
 */
import React, {useContext} from "react";
import "./toolbar.css";
import "../utility.css";
import {SearchOutlined} from "@ant-design/icons";
import {Button, Input, ConfigProvider, Checkbox} from "antd";
import DropdownBranch from "./DropDownBranch";
import {AppContext} from "../../App";
import {CheckboxChangeEvent} from "antd/es/checkbox";

function Toolbar() {
    const props = useContext(AppContext);

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

export default Toolbar;
