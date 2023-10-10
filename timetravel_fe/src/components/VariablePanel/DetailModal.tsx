/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-29 15:49:31
 * @LastEditTime: 2023-08-01 08:33:49
 * @FilePath: /src/components/VariablePanel/DetailModal.tsx
 * @Description:
 */
import React, { useState } from "react";
import { Button, Modal } from "antd";
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
