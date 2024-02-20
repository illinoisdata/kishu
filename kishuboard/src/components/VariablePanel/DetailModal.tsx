import React from "react";
import {Modal} from "antd";

export interface detailModalProps {
    isOpen: boolean;
    html?: string;
    setIsModalOpen: any;
    value: string;
    variableName: string;
}

function renderMultilineText(text: string) {
    // Split the text by newline characters
    const lines = text.split('\n');

    // Map the lines into an array of JSX elements
    return lines.map((line, index) => (
        <React.Fragment key={index}>
            {line}
            {index < lines.length - 1 && <br />} {/* Add a <br /> after each line except the last one */}
        </React.Fragment>
    ));
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
                title={props.variableName}
                open={props.isOpen}
                onOk={handleOk}
                onCancel={handleCancel}
                width={"80%"}
            >
                {/*{props.html ? <div dangerouslySetInnerHTML={{__html: props.html || ''}}/> : <p>{props.value.replaceAll("\\n","\n")}</p>}*/}
                {props.html ? <div dangerouslySetInnerHTML={{__html: props.html || ''}}/> : <p>{props.value.replaceAll("\\n","\n")}</p>}
                {props.html?<div>.....</div>:undefined}
            </Modal>
        </>
    );
}
