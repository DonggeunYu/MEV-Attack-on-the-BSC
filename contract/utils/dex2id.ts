const dex2idJSON = require("../../dex2id.json");

export function dex2id(dex: string): number {
    if (dex2idJSON[dex] == undefined) {
        throw new Error("Invalid dex in dex2id: " + dex);
    }
    return dex2idJSON[dex]["id"];
}

export function dex2name(dex: string): string {
    if (dex2idJSON[dex] == undefined) {
        throw new Error("Invalid dex in dex2name: " + dex);
    }
    return dex2idJSON[dex]["name"];
}
