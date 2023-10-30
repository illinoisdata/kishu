/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-27 16:58:26
 * @LastEditTime: 2023-08-01 10:52:17
 * @FilePath: /src/components/HistoryPanel/TagEditor.tsx
 * @Description:Modal when the user choose to edit the tag for the selected history
 */
import React, {useState} from "react";
import {Modal, Input, Button, message} from "antd";
import {info} from "console";

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
            message.info("setting tag succeed");
            props.setIsModalOpen(false);
        } catch (e) {
            setLoading(false);
            if (e instanceof Error) {
                message.error("tag submit error" + e.message);
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
            title="Create/Edit tag for the selected history"
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
