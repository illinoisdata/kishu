import React, {useState} from "react";
import {Modal, Input, Button, message} from "antd";

export interface TagEditorProps {
    isModalOpen: boolean;
    setIsModalOpen: any;
    submitHandler: (arg: string) => Promise<void>;
    selectedHistoryID?: string;
}

function TagEditor(props: TagEditorProps) {
    const [loading, setLoading] = useState(false);
    const [content, setContent] = useState("");

    async function handleOk() {
        setLoading(true);
        try {
            await props.submitHandler(content);
            setLoading(false);
            message.info("create branch succeed");
            props.setIsModalOpen(false);
        } catch (e) {
            setLoading(false);
            if (e instanceof Error) {
                message.error("branch create error" + e.message);
            }
        }
    }

    const handleCancel = () => {
        props.setIsModalOpen(false);
    };

    const handleChange: any = (event: any) => {
        setContent(event.target.value);
    };

    return (
        <Modal
            title="create a new branch the selected history"
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
