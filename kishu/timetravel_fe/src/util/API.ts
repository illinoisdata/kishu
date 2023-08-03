import { error, time } from "console";
import { History } from "./History";
import { parseAllCommits, parseCommitDetail } from "./parser";
import commits from "../example_jsons/commit_graph.json";
import commit_detail from "../example_jsons/commit.json";

/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 16:36:40
 * @LastEditTime: 2023-08-01 10:50:15
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

  getInitialData() {
    // const histories = fetch(
    //   "/home/meng/elastic-notebook/kishu/timetravel_fe/public/Initialize.json"
    // )
    //   .then((response) => response.json())
    //   .then((data) => parseAllHistories(data))
    //   .catch((error) => console.error("Error fetching data:", error));

    return parseAllCommits(commits);
  },

  getHistoryDetail(historyID: string) {
    // console.log("get:" + historyID);
    // const history = fetch(
    //   "/home/meng/elastic-notebook/kishu/timetravel_fe/public/history.json"
    // )
    //   .then((response) => response.json())
    //   .then((data) => parseHistory(data))
    //   .catch((error) => console.error("Error fetching data:", error));
    return parseCommitDetail(commit_detail);
  },

  setTag(historyID: string, newTag: string) {
    // TODO:call the API to set a tag, if succeed, then...

    let initial_histories = parseAllCommits(commits);
    initial_histories.filter((history) => history.oid === historyID)[0].tag =
      newTag;
    return initial_histories;
  },
};

export { BackEndAPI };
