import React from "react";
import { Variable } from "../../util/Variable";

export interface TableRowNonDiff {
    key: React.ReactNode;
    variableName: string;
    state: string;
    type: string;
    size?: string;
    children: Variable[];
    html?: string;
}

export interface TableRowDiff{
    key: React.ReactNode;
    variableName: string;
    state: string;
    type: string;
    size?: string;
    children: Variable[];
    html?: string;
    option: number;
}

export function GetTableRowNonDiff(variable: Variable): TableRowNonDiff {
    return {
        key: variable.key,
        variableName: variable.variableName,
        state: variable.state,
        type: variable.type,
        size: variable.size,
        children: variable.children,
        html: variable.html,
    };
}

export function GetTableRowDiff(variable: Variable, option: number): TableRowDiff {
    return {
        key: variable.key,
        variableName: variable.variableName,
        state: variable.state,
        type: variable.type,
        size: variable.size,
        children: variable.children,
        html: variable.html,
        option: option,
    };
}