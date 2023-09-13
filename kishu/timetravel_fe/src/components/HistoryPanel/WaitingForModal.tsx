/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-29 15:49:31
 * @LastEditTime: 2023-08-01 08:33:49
 * @FilePath: /src/components/VariablePanel/DetailModal.tsx
 * @Description:
 */
import React, { useState } from "react";
import { Button, Modal } from "antd";
import { LoadingOutlined } from "@ant-design/icons";
import { waitFor } from "@testing-library/react";
export interface waitingforModalProps {
  waitingFor: string;
  isWaitingModalOpen: boolean;
  setIsWaitingModalOpen: any;
  handleCheckout: any;
  handelCreatebranch: any;
}
export function WaitingForModal(props: waitingforModalProps) {
  if (props.isWaitingModalOpen && props.waitingFor === "checkout") {
    props.handleCheckout();
  }
  if (props.isWaitingModalOpen && props.waitingFor === "branch") {
    props.handelCreatebranch();
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
        <LoadingOutlined /> waiting for {props.waitingFor} ...
      </Modal>
    </>
  );
}
