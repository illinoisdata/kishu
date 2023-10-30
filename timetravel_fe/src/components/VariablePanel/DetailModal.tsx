import React from "react";
import {Modal} from "antd";
import "./DetailModal.css";

export interface detailModalProps {
    value?: string;
    isOpen: boolean;
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
                title="Basic Modal"
                open={props.isOpen}
                onOk={handleOk}
                onCancel={handleCancel}
                className="newline"
            >
                <p>{props.value}</p>
            </Modal>
        </>
    );
}
