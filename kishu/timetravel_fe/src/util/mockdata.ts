/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-16 13:01:19
 * @LastEditTime: 2023-07-18 13:50:18
 * @FilePath: /src/util/mockdata.ts
 * @Description:
 */
import { Cell } from "./Cell";
import { History } from "./History";
import { Variable } from "./Variable";
export const MOCK_HISTORIES = [
  new History({
    oid: 1000,
    branchId: 1,
    timestamp: "2023-06-29,15:16:28",
    parentBranchID: -1,
    parentOid: -1,
  }),
  new History({
    oid: 1002,
    branchId: 1,
    timestamp: "2023-06-29,15:16:29",
    parentBranchID: 1,
    parentOid: 1000,
  }),
  new History({
    oid: 1020,
    branchId: 2,
    timestamp: "2023-06-31,15:16:28",
    parentBranchID: 1,
    parentOid: 1000,
  }),
  new History({
    oid: 1003,
    branchId: 1,
    timestamp: "2023-06-29,15:16:30",
    parentBranchID: 1,
    parentOid: 1002,
  }),
  new History({
    oid: 1004,
    branchId: 1,
    timestamp: "2023-06-29,15:16:31",
    parentBranchID: 1,
    parentOid: 1003,
  }),
];

export const MOCK_DETAILED_HISTORIES: Map<Number, History> = new Map([
  [
    1004,
    new History({
      oid: 1004,
      branchId: 1,
      timestamp: "2023-06-29,15:16:31",
      parentBranchID: 1,
      parentOid: 1003,
      execCell: 5001,
      codes: [
        new Cell({
          oid: 5001,
          version: 1004,
          content: "print('hello world')\nprint('goodbye world')",
          execNum: 3,
        }),
        new Cell({
          oid: 5002,
          version: 1003,
          content: "print('hello Supawit')\nprint('goodbye Supawit')",
          execNum: 2,
        }),
        new Cell({
          oid: 5001,
          version: 1004,
          content: "length_c = 5",
          execNum: -1,
        }),
      ],
      variables: [
        new Variable({
          oid: 6000,
          variableName: "length_c",
          version: 1004,
          state: "5",
        }),
        new Variable({
          oid: 5999,
          variableName: "length_b",
          version: 1003,
          state: "6",
        }),
        new Variable({
          oid: 5998,
          variableName: "length_a",
          version: 1003,
          state: "7",
        }),
      ],
    }),
  ],
  [
    1003,
    new History({
      oid: 1003,
      branchId: 1,
      timestamp: "2023-06-29,15:16:30",
      parentBranchID: 1,
      parentOid: 1002,
      execCell: 5001,
      codes: [
        new Cell({
          oid: 5001,
          version: 1003,
          content: "print('hello yongjoo')\nprint('goodbye yongjoo')",
          execNum: 3,
        }),
        new Cell({
          oid: 5002,
          version: 1002,
          content:
            "print('react hooks often lead to some wierd bugs')\nprint('goodbye React, you hurt me')",
          execNum: 2,
        }),
        new Cell({
          oid: 5001,
          version: 1001,
          content: "length_c = 5",
          execNum: 1,
        }),
      ],
      variables: [
        new Variable({
          oid: 6000,
          variableName: "length_c",
          version: 1004,
          state: "5",
        }),
        new Variable({
          oid: 5999,
          variableName: "length_b",
          version: 1003,
          state: "6",
        }),
        new Variable({
          oid: 5998,
          variableName: "length_a",
          version: 1003,
          state: "7",
        }),
      ],
    }),
  ],
  [
    1002,
    new History({
      oid: 1002,
      branchId: 1,
      timestamp: "2023-06-29,15:16:29",
      parentBranchID: 1,
      parentOid: 1000,
      execCell: 5001,
      codes: [
        new Cell({
          oid: 5001,
          version: 1003,
          content:
            "a = 'I like ice-creem'\nb = 'especially in summer'\nc = a + b",
          execNum: 1,
        }),
        new Cell({
          oid: 5002,
          version: 1002,
          content:
            "print('react hooks often lead to some wierd bugs')\nprint('goodbye React, you hurt me')",
          execNum: 2,
        }),
        new Cell({
          oid: 5001,
          version: 1001,
          content: "length_c = 5",
          execNum: 3,
        }),
      ],
      variables: [
        new Variable({
          oid: 6000,
          variableName: "length_c",
          version: 1004,
          state: "5",
        }),
        new Variable({
          oid: 5999,
          variableName: "length_b",
          version: 1003,
          state: "6",
        }),
        new Variable({
          oid: 5998,
          variableName: "length_a",
          version: 1003,
          state: "7",
        }),
      ],
    }),
  ],
]);
