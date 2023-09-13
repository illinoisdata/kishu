/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 11:03:07
 * @LastEditTime: 2023-08-22 23:11:28
 * @FilePath: /src/components/Toolbar/Dropdown.tsx
 * @Description:
 */
import { Select } from "antd";
import { useContext } from "react";
import { AppContext } from "../../App";

function DropdownBranch() {
  const props = useContext(AppContext);
  let options:
    | {
        value: String;
        label: String;
      }[] = [];
  let index: number = 1;

  props!.branchIDs!.forEach((label) => {
    let value = index.toString();
    options.push({ value, label });
    index++;
  });

  return (
    <Select
      showSearch
      style={{ width: 200 }}
      placeholder={props!.selectedBranchID!}
      optionFilterProp="children"
      // eslint-disable-next-line @typescript-eslint/no-unsafe-return
      filterOption={(input, option) => (option?.label ?? "").includes(input)}
      filterSort={(optionA, optionB) =>
        (optionA?.label ?? "")
          .toLowerCase()
          .localeCompare((optionB?.label ?? "").toLowerCase())
      }
      options={options}
      dropdownStyle={{ backgroundColor: "#588157" }}
      onSelect={(value, { value: value1, label }) => {
        props!.setSelectedBranchID(label);
        const commitsInBranch = props!.commits.filter(
          (commit) => commit.branchId === label
        );
        props!.setSelectedCommitID(
          commitsInBranch[commitsInBranch.length - 1].oid
        );
      }}
    />
  );
}

export default DropdownBranch;
