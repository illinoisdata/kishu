/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-29 15:49:31
 * @LastEditTime: 2023-08-01 08:33:49
 * @FilePath: /src/components/VariablePanel/DetailModal.tsx
 * @Description:
 */
import React, { useState } from "react";
import { Button, Modal, message } from "antd";
import { LoadingOutlined } from "@ant-design/icons";
import { waitFor } from "@testing-library/react";
export interface waitingforModalProps {
  checkoutMode: string;
  isWaitingModalOpen: boolean;
  setIsWaitingModalOpen: any;
  checkoutBothHandler: any;
  checkoutVariableHandler: any;
  checkoutBranchID?: string;
  setCheckoutBranchID?: any;
}

// checkoutMode={checkoutMode}
// isWaitingModalOpen={isCheckoutWaitingModelOpen}
// setIsWaitingModalOpen={setIsCheckoutWaitingModelOpen}
// checkoutBothHandler={handleCheckoutBoth}
// checkoutVariableHandler={handleCheckoutVariable}
// checkoutBranchID={checkoutBranchID}
// setCheckoutBranchID={setCheckoutBranchID} //after checkout succeed, the checkoutBranchID will be set to undefined

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
        <LoadingOutlined /> waiting for {props.checkoutMode} ...
      </Modal>
    </>
  );
}
