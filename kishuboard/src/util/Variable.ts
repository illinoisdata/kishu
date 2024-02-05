import React from "react";
export interface Variable {
  key: React.ReactNode;
  variableName: string;
  state: string;
  type: string;
  size?: string;
  children: Variable[];
  html?: string;
}
