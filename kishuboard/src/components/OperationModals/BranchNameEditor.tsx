import React, {useState} from "react";
import {Modal, Input, Button, message} from "antd";

export interface TagEditorProps {
    isModalOpen: boolean;
    setIsModalOpen: any;
    submitHandler: (newBranchName: string, oldBranchName: string|undefined) => Promise<void>;
    selectedHistoryID?: string;
    branchNameToBeEdit: string|undefined;
    setBranchNameToBeEdit: any;
}

function TagEditor(props: TagEditorProps) {
    const [loading, setLoading] = useState(false);
    const [content, setContent] = useState("");

    async function handleOk() {
        setLoading(true);
        try {
            await props.submitHandler(content, props.branchNameToBeEdit);
            setLoading(false);
            message.info(props.branchNameToBeEdit?"rename branch succeed":"create branch succeed");
            props.setBranchNameToBeEdit(undefined);
            props.setIsModalOpen(false);
        } catch (e) {
            setLoading(false);
            if (e instanceof Error) {
                message.error("branch edit error" + e.message);
            }
        }
    }

    const handleCancel = () => {
        props.setIsModalOpen(false);
        props.setBranchNameToBeEdit(undefined);
    };

    const handleChange: any = (event: any) => {
        setContent(event.target.value);
    };

    return (
        <Modal
            title={props.branchNameToBeEdit?"Change the branch name for branch "+props.branchNameToBeEdit!:"Create a new branch for the selected history"}
            open={props.isModalOpen}
            onOk={handleOk}
            onCancel={handleCancel}
            footer={[
                <Button key="back" onClick={handleCancel}>
                    Return
                </Button>,
                <Button
                    key="submit"
                    type="primary"
                    loading={loading}
                    onClick={handleOk}
                >
                    Submit
                </Button>,
            ]}
        >
            <Input onChange={handleChange} value={content}/>
        </Modal>
    );
}

export default TagEditor;
