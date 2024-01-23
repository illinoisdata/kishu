import {message} from "antd";
import React, {ChangeEventHandler} from "react";
import Search from "antd/es/input/Search";
import {BackEndAPI} from "../../util/API";

export interface SearchBarProps {
    setHighlightedCommitIds: any;
}

function getOperation(value: string): string {
    return "filter";
}

function getKeyInfo(operation: string, value: string): string {
    return value;
}

async function ExecuteOperation(operation: string, keyInfo: string) {
    return await BackEndAPI.getFilteredCommit(keyInfo);
}

function _SearchBar({setHighlightedCommitIds}: SearchBarProps) {
    const searchHandler = async (value: string) => {
        try {
            if(value === ""){
                setHighlightedCommitIds([]);
                return;
            }
            const operation = getOperation(value);
            const keyInfo = getKeyInfo(operation, value);
            const result = await ExecuteOperation(operation, keyInfo);
            setHighlightedCommitIds(result);
        } catch (e) {
            message.error("search error: " + (e as Error).message);
        }
    }

    const handleChange: ChangeEventHandler<HTMLInputElement> = (e) => {
        if(e.target.value === ""){
            setHighlightedCommitIds([]);
        }
    }
    return (
        <div className="searchBar">
            <Search placeholder="input search text" allowClear onSearch={searchHandler} onChange={handleChange}/>
        </div>)
}

export const SearchBar = React.memo(_SearchBar);