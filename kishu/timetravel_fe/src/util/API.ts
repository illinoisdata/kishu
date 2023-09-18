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
        throw new Error("backend error, status != OK");
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

  async getCommitGraph() {
    const res = await fetch("/fe/commit_graph/" + globalThis.NotebookID!);
    try {
      const data = await res.json();
      console.log(data);
      return parseAllCommits(data);
    } catch (error) {
      throw error;
    }
  },

  async getCommitDetail(commitID: string) {
    const res = await fetch(
      "/fe/commit/" + globalThis.NotebookID! + "/" + commitID
    );
    try {
      const data = await res.json();
      console.log(data);
      return parseCommitDetail(data);
    } catch (error) {
      return console.error("Error fetching data:", error);
    }
  },

  async setTag(commitID: string, newTag: string) {
    // message.info(`rollback succeeds`);
    // TODO: call backend API according to API
    const res = await fetch(
      "/tag/" +
        globalThis.NotebookID! +
        "?commit_id=" +
        commitID +
        "&tag=" +
        newTag
    );
    try {
      const data = await res.json();
      if (data.status === "ok") {
        console.log("set tag done");
      } else {
        console.log(data);
        throw Error("Setting tag failed, state != OK");
      }
    } catch (error) {
      throw error;
    }
  },

  async createBranch(commitID: string, newBranchname: string) {
    // message.info(`rollback succeeds`);
    const res = await fetch(
      "/branch/" +
        globalThis.NotebookID! +
        "/" +
        newBranchname +
        "?commit_id=" +
        commitID
    );
    try {
      const data = await res.json();
      if (data.status === "ok") {
        console.log("creating branch done");
      } else {
        console.log(data);
        throw Error("create branch failed, state != OK");
      }
    } catch (error) {
      throw error;
    }
  },
};

export { BackEndAPI };
