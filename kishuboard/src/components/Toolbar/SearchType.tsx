import {Select} from "antd";

export interface SearchTypeProps {
    type: string;
    setType: any;
}
export function SearchType(props: SearchTypeProps) {
    const selectionBar = <Select
        style={{width: "50%"}}
        placeholder="Select search target"
        onChange={(value)=>{props.setType(value)}}
        options={[
            {
                value: 'all',
                label: 'all',
            },
            {
                value: 'variable change',
                label: 'variable change',
            },
            {
                value: 'commit message',
                label: 'commit message',
            },
            {
                value: 'commit tag',
                label: 'commit tag',
            },
        ]}
    />

    return (
        <>
            {selectionBar}
        </>
    );
}