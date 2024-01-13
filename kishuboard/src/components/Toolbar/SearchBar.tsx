import {message} from "antd";
import React, {ChangeEventHandler, useContext} from "react";
import Search from "antd/es/input/Search";
import {BackEndAPI} from "../../util/API";
import {SearchType} from "./SearchType";
import {AppContext} from "../../App";
import {Commit} from "../../util/Commit";

export interface SearchBarProps {
    setHighlightedCommitIds: any;
    searchType: string;
    setSearchType: any;
    setScrollToHighlight: any;
    currentSignal: boolean;
}

function getOperation(value: string): string {
    return "filter";
}

function getKeyInfo(operation: string, value: string): string {
    return value;
}

async function ExecuteOperation(searchType: string, keyInfo: string, commits:Commit[]) {
    console.log("type:", searchType)
    if (searchType === "variable change") {
        return await BackEndAPI.getFilteredCommit(keyInfo);
    }
    if (searchType === "commit message") {
        return commits.filter((commit) => {
            return commit.message.includes(keyInfo);
        }).map((commit) => {
            return commit.oid;
        });
    }
    if (searchType === "commit tag") {
        return commits.filter((commit) => {
            return commit.tags.includes(keyInfo);
        }).map((commit) => {
            return commit.oid;
        })
    }
    if (searchType === "all") {
         const metaDataFiltered =  commits.filter((commit) => {
            return commit.message.includes(keyInfo) || commit.tags.includes(keyInfo);
        }).map((commit) => {
            return commit.oid;
        });

         const varChangeFiltered = await BackEndAPI.getFilteredCommit(keyInfo);
         return metaDataFiltered.concat(varChangeFiltered);
    }

}

function _SearchBar(props: SearchBarProps) {
    const appProps = useContext(AppContext);
    const searchHandler = async (value: string) => {
        try {
            if(value === ""){
                props.setHighlightedCommitIds([]);
                return;
            }
            const result = await ExecuteOperation(props.searchType, value, appProps!.commits);
            props.setScrollToHighlight(!props.currentSignal);//change the signal to trigger the scroll of history panel
            props.setHighlightedCommitIds(result);
        } catch (e) {
            message.error("search error: " + (e as Error).message);
        }
    }

    const handleChange: ChangeEventHandler<HTMLInputElement> = (e) => {
        if(e.target.value === ""){
            props.setHighlightedCommitIds([]);
        }
    }
    return (
        <div className="searchBar">
            <SearchType type={props.searchType} setType={props.setSearchType} />
            <Search placeholder="input search text" allowClear onSearch={searchHandler} onChange={handleChange}/>
        </div>)
}

export const SearchBar = React.memo(_SearchBar);