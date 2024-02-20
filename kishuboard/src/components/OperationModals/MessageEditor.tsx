import React, {useState} from "react";
import {Modal, Input, Button, message} from "antd";

export interface MessageEditorProps {
    isModalOpen: boolean;
    setIsModalOpen: any;
    submitHandler: (arg: string) => Promise<void>;
    selectedHistoryID?: string;
    currentMessage?: string;
}

function MessageEditor(props: MessageEditorProps) {
    const [loading, setLoading] = useState(false);
    const [content, setContent] = useState(props.currentMessage?props.currentMessage:"");

    async function handleOk() {
        setLoading(true);
        try {
            await props.submitHandler(content);
            setLoading(false);
            message.info("Edit commit message succeed");
            props.setIsModalOpen(false);
        } catch (e) {
            setLoading(false);
            if (e instanceof Error) {
                message.error("Edit commit message error" + e.message);
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
            title="Edit the commit message for the selected history"
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

export default MessageEditor;
