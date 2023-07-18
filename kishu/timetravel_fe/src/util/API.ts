import { error, time } from "console";
import { History } from "./History";
import { MOCK_HISTORIES, MOCK_DETAILED_HISTORIES } from "./mockdata";

/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 16:36:40
 * @LastEditTime: 2023-07-18 14:12:27
 * @FilePath: /src/util/API.ts
 * @Description:
 */

const BackEndAPI = {
  rollbackBoth(historyID: number) {
    return new Promise((resolve) => setTimeout(resolve, 1000));
    // message.info(`rollback succeeds`);
  },

  rollbackCodes(historyID: number) {
    // message.info(`rollback succeeds`);
  },

  rollbackVariables(historyID: number) {
    // message.info(`rollback succeeds`);
  },

  getInitialData(): { histories: History[]; selectedID: number } {
    return { histories: MOCK_HISTORIES, selectedID: 1004 };
  },

  getHistoryDetail(historyID: number): History {
    console.log("get:" + historyID);
    const result = MOCK_DETAILED_HISTORIES.get(historyID);
    console.log(result);
    if (!result) {
      throw new Error("The detail information of this history doesn't exist!");
    }
    return result!;
  },
};

export { BackEndAPI };
