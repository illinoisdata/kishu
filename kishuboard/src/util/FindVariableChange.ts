import { Variable } from "./Variable";

// find if two variables are equal without consider the children variables
export function JudgeVariableEqual(
  previousVariable: Variable,
  newVariable: Variable
) {
  if (previousVariable.type !== newVariable.type) {
    return false;
  }
  if (previousVariable.size && previousVariable.size !== newVariable.size) {
    return false;
  }
  return previousVariable.state === newVariable.state;

}
