import React from "react";
import {Modal, message} from "antd";
import {LoadingOutlined} from "@ant-design/icons";

export interface waitingforModalProps {
    checkoutMode: string;
    isWaitingModalOpen: boolean;
    setIsWaitingModalOpen: any;
    checkoutBothHandler: any;
    checkoutVariableHandler: any;
    checkoutBranchID?: string;
    setCheckoutBranchID?: any;
}

export function CheckoutWaitingModal(props: waitingforModalProps) {
    async function handleCheckout() {
        try {
            if (props.checkoutMode === "checkout codes and data") {
                await props.checkoutBothHandler(props.checkoutBranchID);
            } else if (props.checkoutMode === "checkout variables only") {
                await props.checkoutVariableHandler(props.checkoutBranchID);
            }
            props.setIsWaitingModalOpen(false);
            message.info("checkout succeed");
            props.setCheckoutBranchID(undefined);
        } catch (e) {
            props.setIsWaitingModalOpen(false);
            props.setCheckoutBranchID(undefined);
            message.error("checkout error: " + (e as Error).message);
        }
    }

    if (props.isWaitingModalOpen) {
        handleCheckout();
    }
    return (
        <>
            <Modal
                title={null}
                open={props.isWaitingModalOpen}
                footer={null}
                closeIcon={null}
                centered={true}
            >
                <LoadingOutlined/> waiting for {props.checkoutMode} ...
            </Modal>
        </>
    );
}
