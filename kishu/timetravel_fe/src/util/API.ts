import { error, time } from "console";
import { Commit } from "./Commit";
import { parseAllCommits, parseCommitDetail } from "./parser";
import commits from "../example_jsons/commit_graph.json";
import commit_detail from "../example_jsons/commit.json";
import { message } from "antd";

/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-07-14 16:36:40
 * @LastEditTime: 2023-08-01 10:50:15
 * @FilePath: /src/util/API.ts
 * @Description:
 */

const BackEndAPI = {
  async rollbackBoth(historyID: string) {
    // message.info(`rollback succeeds`);
    const res = await fetch(
      "/checkout/" + globalThis.NotebookID! + "/" + historyID
    );
    try {
      const data = await res.json();
      if (data.status === "ok") {
        console.log("checkout done");
      } else {
        console.log(data);
        throw new Error("backend error");
      }
    } catch (error) {
      throw error;
    }
  },

  rollbackCodes(historyID: number) {
    // message.info(`rollback succeeds`);
  },

  rollbackVariables(historyID: number) {
    // message.info(`rollback succeeds`);
  },

  async getInitialData() {
    const res = await fetch("/fe/commit_graph/" + globalThis.NotebookID!);
    try {
      const data = await res.json();
      return parseAllCommits(data);
    } catch (error) {
      throw error;
    }

    // return fetch("/fe/commit_graph/" + globalThis.NotebookID!)
    //   .then((res) => {
    //     res.json();
    //   })
    //   .then((data) => parseAllCommits(data))
    //   .catch((error) => console.error("Error fetching data:", error));

    // return parseAllCommits(commits);
  },

  async getCommitDetail(historyID: string) {
    // console.log("get:" + historyID);
    // const history = fetch(
    //   "/home/meng/elastic-notebook/kishu/timetravel_fe/public/history.json"
    // )
    //   .then((response) => response.json())
    //   .then((data) => parseHistory(data))
    //   .catch((error) => console.error("Error fetching data:", error));
    // return parseCommitDetail(commit_detail);

    const res = await fetch(
      "/fe/commit/" + globalThis.NotebookID! + "/" + historyID
    );
    try {
      const data = await res.json();
      return parseCommitDetail(data);
    } catch (error) {
      return console.error("Error fetching data:", error);
    }
  },

  setTag(historyID: string, newTag: string) {
    // TODO:call the API to set a tag, if succeed, then...

    let initial_histories = parseAllCommits(commits);
    initial_histories.filter((history) => history.oid === historyID)[0].tag =
      newTag;
    return initial_histories;
  },

  async createBranch(commitID: string, newBranchname: string) {
    // message.info(`rollback succeeds`);
    const res = await fetch(
      "/branch/" + globalThis.NotebookID! + "/" + newBranchname + "/" + commitID
    );
    try {
      const data = await res.json();
      if (data.status === "ok") {
        console.log("creating branch done");
      } else {
        console.log(data);
        throw new Error("backend error");
      }
    } catch (error) {
      throw error;
    }
  },
};

export { BackEndAPI };
