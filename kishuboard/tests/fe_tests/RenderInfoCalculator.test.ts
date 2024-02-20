import {VisInfoManager, TopologyCommitType, RenderInfoCalculator} from '../../src/util/getPointRenderInfo';
import { Commit } from '../../src/util/Commit';
import {render} from "@testing-library/react";

describe('testing_ass_type2commit', () => {
    test("test_all_types",()=>{
        const commits = [
            {
                oid: "10",
                parentOid: "9",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:19",
                codeVersion: "10",
                variableVersion: "10"
            } as Commit,
            {
                oid: "9",
                parentOid: "6",
                message: "Auto commit",
                tags: ["abbc"],
                branchIds: [],
                timestamp: "2023-07-16 11:49:14",
                codeVersion: "9",
                variableVersion: "9"
            } as Commit,
            {
                oid: "8",
                parentOid: "7",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:09",
                codeVersion: "8",
                variableVersion: "8"
            } as Commit,
            {
                oid: "7",
                parentOid: "5",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:04",
                codeVersion: "7",
                variableVersion: "7"
            } as Commit,
            {
                oid: "6",
                parentOid: "5",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:59",
                codeVersion: "6",
                variableVersion: "6"
            } as Commit,
            {
                oid: "5",
                parentOid: "4",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:54",
                codeVersion: "5",
                variableVersion: "5"
            } as Commit,
            {
                oid: "4",
                parentOid: "3",
                message: "Auto commit",
                tags: ["abbc"],
                branchIds: [],
                timestamp: "2023-07-16 11:48:49",
                codeVersion: "4",
                variableVersion: "4"
            } as Commit,
            {
                oid: "3",
                parentOid: "2",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:44",
                codeVersion: "3",
                variableVersion: "3"
            } as Commit,
            {
                oid: "2",
                parentOid: "1",
                message: "Auto commit",
                tags: [],
                branchIds: ["branch1"],
                timestamp: "2023-07-16 11:48:39",
                codeVersion: "2",
                variableVersion: "2"
            } as Commit,
            {
                oid: "1",
                parentOid: "-1",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:34",
                codeVersion: "1",
                variableVersion: "1"
            } as Commit
        ]
        const cal = new VisInfoManager(commits,undefined);
        const topologyType = cal.getTopologyType()
        expect(topologyType).toStrictEqual([TopologyCommitType.LEAF,TopologyCommitType.USERIMPL,TopologyCommitType.LEAF,TopologyCommitType.NORMAL,TopologyCommitType.NORMAL,TopologyCommitType.BRANCH,TopologyCommitType.USERIMPL,TopologyCommitType.NORMAL,TopologyCommitType.USERIMPL,TopologyCommitType.ROOT])
    })
})

describe('testing group', () => {
    test('test_group_NORMAL', () => {
        const commits = [
            {
                oid: "10",
                parentOid: "9",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:19",
                codeVersion: "10",
                variableVersion: "10"
            } as Commit,
            {
                oid: "9",
                parentOid: "6",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:14",
                codeVersion: "9",
                variableVersion: "9"
            } as Commit,
            {
                oid: "8",
                parentOid: "7",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:09",
                codeVersion: "8",
                variableVersion: "8"
            } as Commit,
            {
                oid: "7",
                parentOid: "5",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:04",
                codeVersion: "7",
                variableVersion: "7"
            } as Commit,
            {
                oid: "6",
                parentOid: "5",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:59",
                codeVersion: "6",
                variableVersion: "6"
            } as Commit,
            {
                oid: "5",
                parentOid: "-1",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:54",
                codeVersion: "5",
                variableVersion: "5"
            }
        ]

        const cal = new VisInfoManager(commits,undefined);
        const groupInfo = cal.getGroupInfo()
        expect(groupInfo.maxGroupID).toBe(4);
    });

    test('test_group_USERIMPL', () => {
        const commits = [
            {
                oid: "10",
                parentOid: "9",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:19",
                codeVersion: "10",
                variableVersion: "10"
            } as Commit,
            {
                oid: "9",
                parentOid: "6",
                message: "Auto commit",
                tags: ["abbc"],
                branchIds: [],
                timestamp: "2023-07-16 11:49:14",
                codeVersion: "9",
                variableVersion: "9"
            } as Commit,
            {
                oid: "8",
                parentOid: "7",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:09",
                codeVersion: "8",
                variableVersion: "8"
            } as Commit,
            {
                oid: "7",
                parentOid: "5",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:04",
                codeVersion: "7",
                variableVersion: "7"
            } as Commit,
            {
                oid: "6",
                parentOid: "5",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:59",
                codeVersion: "6",
                variableVersion: "6"
            } as Commit,
            {
                oid: "5",
                parentOid: "4",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:54",
                codeVersion: "5",
                variableVersion: "5"
            } as Commit,
            {
                oid: "4",
                parentOid: "3",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:49",
                codeVersion: "4",
                variableVersion: "4"
            } as Commit,
            {
                oid: "3",
                parentOid: "2",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:44",
                codeVersion: "3",
                variableVersion: "3"
            } as Commit,
            {
                oid: "2",
                parentOid: "1",
                message: "Auto commit",
                tags: [],
                branchIds: ["branch1"],
                timestamp: "2023-07-16 11:48:39",
                codeVersion: "2",
                variableVersion: "2"
            } as Commit,
            {
                oid: "1",
                parentOid: "-1",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:34",
                codeVersion: "1",
                variableVersion: "1"
            } as Commit
        ]
        const cal = new VisInfoManager(commits,undefined);
        const groupInfo = cal.getGroupInfo()
        expect(groupInfo.maxGroupID).toBe(9);
    });

    test('test_group_NEWDAY4BRANCH', () => {
        const commits = [
            {
                oid: "10",
                parentOid: "9",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:19",
                codeVersion: "10",
                variableVersion: "10"
            } as Commit,
            {
                oid: "9",
                parentOid: "6",
                message: "Auto commit",
                tags: ["abbc"],
                branchIds: [],
                timestamp: "2023-07-16 11:49:14",
                codeVersion: "9",
                variableVersion: "9"
            } as Commit,
            {
                oid: "8",
                parentOid: "7",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:09",
                codeVersion: "8",
                variableVersion: "8"
            } as Commit,
            {
                oid: "7",
                parentOid: "5",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:49:04",
                codeVersion: "7",
                variableVersion: "7"
            } as Commit,
            {
                oid: "6",
                parentOid: "5",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:59",
                codeVersion: "6",
                variableVersion: "6"
            } as Commit,
            {
                oid: "5",
                parentOid: "4",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:54",
                codeVersion: "5",
                variableVersion: "5"
            } as Commit,
            {
                oid: "4",
                parentOid: "3",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-16 11:48:49",
                codeVersion: "4",
                variableVersion: "4"
            } as Commit,
            {
                oid: "3",
                parentOid: "2",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-15 11:48:44",
                codeVersion: "3",
                variableVersion: "3"
            } as Commit,
            {
                oid: "2",
                parentOid: "1",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-15 11:48:39",
                codeVersion: "2",
                variableVersion: "2"
            } as Commit,
            {
                oid: "1",
                parentOid: "-1",
                message: "Auto commit",
                tags: [],
                branchIds: [],
                timestamp: "2023-07-15 11:48:34",
                codeVersion: "1",
                variableVersion: "1"
            } as Commit
        ]
        const cal = new VisInfoManager(commits,undefined);
        const groupInfo = cal.getGroupInfo()
        expect(groupInfo.maxGroupID).toBe(10);
    });

});

describe("testing cal visualization and render information",()=>{
    const commits = [
        {
            oid: "10",
            parentOid: "9",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:49:19",
            codeVersion: "10",
            variableVersion: "10"
        } as Commit,
        {
            oid: "9",
            parentOid: "6",
            message: "Auto commit",
            tags: ["abbc"],
            branchIds: [],
            timestamp: "2023-07-16 11:49:14",
            codeVersion: "9",
            variableVersion: "9"
        } as Commit,
        {
            oid: "8",
            parentOid: "7",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:49:09",
            codeVersion: "8",
            variableVersion: "8"
        } as Commit,
        {
            oid: "7",
            parentOid: "5",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:49:04",
            codeVersion: "7",
            variableVersion: "7"
        } as Commit,
        {
            oid: "6",
            parentOid: "5",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:48:59",
            codeVersion: "6",
            variableVersion: "6"
        } as Commit,
        {
            oid: "5",
            parentOid: "4",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:48:54",
            codeVersion: "5",
            variableVersion: "5"
        } as Commit,
        {
            oid: "4",
            parentOid: "3",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:48:49",
            codeVersion: "4",
            variableVersion: "4"
        } as Commit,
        {
            oid: "3",
            parentOid: "2",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:48:44",
            codeVersion: "3",
            variableVersion: "3"
        } as Commit,
        {
            oid: "2",
            parentOid: "1",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:48:39",
            codeVersion: "2",
            variableVersion: "2"
        } as Commit,
        {
            oid: "1",
            parentOid: "-1",
            message: "Auto commit",
            tags: [],
            branchIds: [],
            timestamp: "2023-07-16 11:48:34",
            codeVersion: "1",
            variableVersion: "1"
        } as Commit
    ]
    const cal = new VisInfoManager(commits,undefined);
    const groupInfo = cal.getGroupInfo()
    const maxGroupID = groupInfo.maxGroupID

    const isGroupFolded:Map<number,boolean> = new Map()
    for (let i = 1; i <= maxGroupID; i++) {
        isGroupFolded.set(i, true)
    }
    test("calculate vis points",()=>{
        const visPoints = cal.getVisPoints(isGroupFolded)
        expect(visPoints.length).toBe(8);
    })

    test("calculate render info",() => {
        const visPoints = cal.getVisPoints(isGroupFolded)
        const renderInfoCalculator = new RenderInfoCalculator(visPoints,undefined)
        const renderInfo = renderInfoCalculator.getPointRenderInfo()
        expect(renderInfo.maxX).toBe(30);
    })
});
