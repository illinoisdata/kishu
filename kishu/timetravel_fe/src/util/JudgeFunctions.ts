//judge if a certain history belongs to a group

import { History } from "./History";

export const Judger = {
  JudgeGroupByTag(history: History): boolean {
    const tagged =
      history !== undefined &&
      history.tag !== null &&
      history.tag !== "" &&
      history.tag !== undefined;
    return !tagged; //all histories that are not tagged belong to a certain group
  },

  JudgeGroupByNoGroup(history: History) {
    return false;
  },
  JudgeGroupBySearch(history: History) {
    return false;
  },
};
