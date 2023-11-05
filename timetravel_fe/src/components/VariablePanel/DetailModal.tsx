import React from "react";
import {Modal} from "antd";
import "./DetailModal.css";

export interface detailModalProps {
    value?: string;
    isOpen: boolean;
    html?: string;
    setIsModalOpen: any;
}

export function DetailModal(props: detailModalProps) {
    const handleOk = () => {
        props.setIsModalOpen(false);
    };

    const handleCancel = () => {
        props.setIsModalOpen(false);
    };

    return (
        <>
            <Modal
                title="Variable Detail"
                open={props.isOpen}
                onOk={handleOk}
                onCancel={handleCancel}
                // className="newline"
                width={"80%"}
                // className={"newline"}
            >
                {props.html ? <div dangerouslySetInnerHTML={{__html: props.html || ''}}/> : <p>props.value</p>}
                <div>.....</div>
            </Modal>
        </>
    );
}
