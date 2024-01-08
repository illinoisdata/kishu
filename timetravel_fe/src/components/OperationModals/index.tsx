import React, {useContext} from "react";
import {OperationModelContext} from "../../App";
import TagEditor from "./TagEditor";
import BranchNameEditor from "./BranchNameEditor";
import {CheckoutBranchModel} from "./CheckoutBranchModel";
import {CheckoutWaitingModal} from "./CheckoutWaitingForModal";
import {BackEndAPI} from "../../util/API";
import {CommitDetail} from "../../util/Commit";

export interface OperationModalProps {
    refreshGraphHandler: any;
    selectedCommitID: string
    selectedCommit: CommitDetail
}

export function OperationModals(props: OperationModalProps) {
    const modelOpenContext = useContext(OperationModelContext)!

    async function handleTagSubmit(newTag: string) {
        try {
            await BackEndAPI.setTag(props.selectedCommitID!!, newTag);
            props.refreshGraphHandler();
        } catch (error) {
            throw error;
        }
    }
    //metadata, tracing, visitor,attach, detach?

    async function handleBranchNameSubmit(newBranchName: string) {
        try {
            await BackEndAPI.createBranch(props!.selectedCommitID!, newBranchName);
            props.refreshGraphHandler();
        } catch (error) {
            throw error;
        }
    }

    async function handleCheckoutBoth(branchID?: string) {
        try {
            await BackEndAPI.rollbackBoth(props!.selectedCommitID!, branchID);
            props.refreshGraphHandler();
        } catch (error) {
            throw error;
        }
    }

    async function handleCheckoutVariable(branchID?: string) {
        try {
            await BackEndAPI.rollbackVariables(props!.selectedCommitID!, branchID);
            props.refreshGraphHandler();
        } catch (error) {
            throw error;
        }
    }
    return <>
        {modelOpenContext.isTagEditorOpen && (<TagEditor
            isModalOpen={modelOpenContext.isTagEditorOpen}
            setIsModalOpen={modelOpenContext.setIsTagEditorOpen}
            submitHandler={handleTagSubmit}
            selectedHistoryID={props!.selectedCommitID!}
        ></TagEditor>)}
        {modelOpenContext.isBranchNameEditorOpen && <BranchNameEditor
            isModalOpen={modelOpenContext.isBranchNameEditorOpen}
            setIsModalOpen={modelOpenContext.setIsBranchNameEditorOpen}
            submitHandler={handleBranchNameSubmit}
            selectedHistoryID={props!.selectedCommitID!}
        ></BranchNameEditor>}
        {modelOpenContext.chooseCheckoutBranchModalOpen && <CheckoutBranchModel
            branchIDOptions={props.selectedCommit?.commit.branchIds}
            isModalOpen={modelOpenContext.chooseCheckoutBranchModalOpen}
            setCheckoutBranchID={modelOpenContext.setCheckoutBranchID}
            setIsCheckoutWaitingModalOpen={modelOpenContext.setIsCheckoutWaitingModalOpen}
            setIsModalOpen={modelOpenContext.setChooseCheckoutBranchModalOpen}
        ></CheckoutBranchModel>}
        {modelOpenContext.isCheckoutWaitingModalOpen && <CheckoutWaitingModal
            checkoutMode={modelOpenContext.checkoutMode}
            isWaitingModalOpen={modelOpenContext.isCheckoutWaitingModalOpen}
            setIsWaitingModalOpen={modelOpenContext.setIsCheckoutWaitingModalOpen}
            checkoutBothHandler={handleCheckoutBoth}
            checkoutVariableHandler={handleCheckoutVariable}
            checkoutBranchID={modelOpenContext.checkoutBranchID}
            setCheckoutBranchID={modelOpenContext.setCheckoutBranchID} //after checkout succeed, the checkoutBranchID will be set to undefined
        ></CheckoutWaitingModal>}
    </>;
}

