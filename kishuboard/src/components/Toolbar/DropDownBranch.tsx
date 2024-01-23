import {Select} from "antd";
import {useContext} from "react";
import {AppContext} from "../../App";

function DropdownBranch() {
    const props = useContext(AppContext);
    let options: {
        value: string;
        label: string;
    }[] = [];
    let index: number = 1;

    props!.branchID2CommitMap.forEach((commit, label) => {
        let value = index.toString();
        options.push({value, label});
        index++;
    });

    return (
        <Select
            showSearch
            // placeholder={props!.selectedBranchID!}
            placeholder={"current branch: " + props!.selectedBranchID!}
            optionFilterProp="children"
            // eslint-disable-next-line @typescript-eslint/no-unsafe-return
            filterOption={(input, option) => (option?.label ?? "").includes(input)}
            filterSort={(optionA, optionB) =>
                (optionA?.label ?? "")
                    .toLowerCase()
                    .localeCompare((optionB?.label ?? "").toLowerCase())
            }
            options={options}
            onSelect={(value, {value: value1, label}) => {
                props?.setSelectedCommitID(props?.branchID2CommitMap.get(label));
                props?.setSelectedBranchID(label);
            }}
        />
    );
}

export default DropdownBranch;
