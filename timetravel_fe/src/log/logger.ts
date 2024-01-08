import { Logger,ILogObj } from "tslog";
const logLevel = process.env.LOG_LEVEL

export const logger: Logger<ILogObj>= new Logger({
    minLevel: 4
});
