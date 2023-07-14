import { time } from "console";

/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 16:36:40
 * @LastEditTime: 2023-07-14 16:59:46
 * @FilePath: /src/util/API.ts
 * @Description:
 */
const BackEndAPI = {
  rollbackBoth(historyID: Number) {
    let fun = () => console.log("time out");
    let sleep2 = (time: number) =>
      new Promise((resolve) => {
        setTimeout(resolve, time);
      });
    sleep2(2000).then(fun);
    // message.info(`rollback succeeds`);
  },

  rollbackCodes(historyID: Number) {
    // message.info(`rollback succeeds`);
  },

  rollbackVariables(historyID: Number) {
    // message.info(`rollback succeeds`);
  },
};

export { BackEndAPI };
