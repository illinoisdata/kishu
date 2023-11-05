/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-27 16:58:26
 * @LastEditTime: 2023-08-01 10:52:17
 * @FilePath: /src/components/HistoryPanel/TagEditor.tsx
 * @Description:Modal when the user choose to edit the tag for the selected history
 */
import React, {useState} from "react";
import {Modal, Select} from "antd";

export interface CheckoutBranchModelProps {
    isModalOpen: boolean;
    setIsModalOpen: any;
    branchIDOptions?: string[];
    setCheckoutBranchID: any;
    setIsCheckoutWaitingModalOpen: any;
}

export function CheckoutBranchModel(props: CheckoutBranchModelProps) {
    const [content, setContent] = useState(
        props.branchIDOptions ? props.branchIDOptions[0] : "",
    );

    async function handleOk() {
        props.setCheckoutBranchID(content);
        props.setIsModalOpen(false);
        props.setIsCheckoutWaitingModalOpen(true);
    }

    const handleCancel = () => {
        props.setIsModalOpen(false);
    };

    const handleChange = (value: string) => {
        setContent(value);
    };

    return (
        <Modal onCancel={handleCancel} onOk={handleOk} open={props.isModalOpen}>
            <Select
                defaultValue={props.branchIDOptions ? props.branchIDOptions[0] : ""}
                style={{width: "80%"}}
                onChange={handleChange}
                options={props.branchIDOptions?.map((branchID) => {
                    return {value: branchID, label: branchID};
                })}
            />
        </Modal>
    );
}
