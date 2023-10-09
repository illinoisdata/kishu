/* eslint-disable import/no-extraneous-dependencies */
/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 13:35:06
 * @LastEditTime: 2023-07-14 12:02:12
 * @FilePath: /src/components/SearchPanel/index.tsx
 * @Description:a history point to represent one snapshot in the history panel
 */
import { SearchOutlined } from "@ant-design/icons";
import { Input, Button, Space } from "antd";
import "../utility.css";

const { TextArea } = Input;

const SearchPanel: React.FC = () => {
  return (
    <>
      <div className="u-fullWidthDiv">
        <TextArea rows={16} />
        <div className="u-central">
          <Button type="primary" icon={<SearchOutlined rev={undefined} />}>
            Search
          </Button>
        </div>
      </div>
      {/* <div>
        <Button type="primary" icon={<SearchOutlined rev={undefined} />}>
          Search
        </Button>
      </div> */}
    </>
  );
};

export default SearchPanel;
