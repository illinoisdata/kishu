import { Logger,ILogObj } from "tslog";

export const logger: Logger<ILogObj>= new Logger({
    minLevel: 4
});
