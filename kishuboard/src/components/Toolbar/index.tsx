import React from "react";
import "./toolbar.css";
import "../utility.css";
import {Input, ConfigProvider, Checkbox} from "antd";
import DropdownBranch from "./DropDownBranch";
import {CheckboxChangeEvent} from "antd/es/checkbox";
import {SearchBar} from "./SearchBar";
import {SearchType} from "./SearchType";

export interface toolBarProps{
    // setInDiffMode: any;
    setSearchResultIds: any;
    setScrollToHighlightSignal:any;
    currentSignal:boolean;
}

function _Toolbar(props: toolBarProps) {
    // const onDiffModeChange = (e: CheckboxChangeEvent) => {
    //     props?.setInDiffMode(e.target.checked);
    // };

    const [searchType, setSearchType] = React.useState<string>("all");

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
                        placeholder={"Name: " + globalThis.NotebookName}
                        disabled={true}
                        style={{width: "20%"}}
                    />

                    <SearchBar setHighlightedCommitIds={props.setSearchResultIds} searchType={searchType} setSearchType={setSearchType} setScrollToHighlight={props.setScrollToHighlightSignal} currentSignal={props.currentSignal}/>

                    {/*<Checkbox onChange={onDiffModeChange}>DiffMode</Checkbox>*/}


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
