import fetchMock from "fetch-mock";
import { BackEndAPI } from "../../src/util/API"; // Adjust the import path based on your setup
import { parseCommitGraph, parseCommitDetail} from "../../src/util/parser";

// Mocking the URL globally
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:4999';
globalThis.NotebookPath = "some_notebook_path";

describe("BackEndAPI tests", () => {

    afterEach(() => {
        fetchMock.restore();
    });

    it("should call rollbackBoth successfully", async () => {
        fetchMock.get(`${BACKEND_URL}/api/checkout?notebook_path=some_notebook_path&branch_or_commit_id=123&skip_notebook=False`, 200);
        await expect(BackEndAPI.rollbackBoth("123")).resolves.toBeUndefined();
        expect(fetchMock.calls()).toHaveLength(1);
    });

    it("should throw error if rollbackBoth fails", async () => {
        fetchMock.get(`${BACKEND_URL}/api/checkout?notebook_path=some_notebook_path&branch_or_commit_id=123&skip_notebook=False`, 500);

        await expect(BackEndAPI.rollbackBoth("123")).rejects.toThrow("rollback backend error, status != OK");
    });

    it("should parse commit graph correctly", async () => {
        const mockResponse = {
            commits: [
                {
                    oid: "abc123",
                    branches: ["branch1", "branch2"],
                    timestamp: "2023-10-22T12:34:56Z",
                    parent_oid: "def456",
                    nb_parent_oid: "ghi789",
                    tags: ["v1.0", "v1.1"],
                    code_version: "v2.0",
                    varset_version: "v1.0",
                    message: "Initial commit",
                },
                {
                    oid: "def456",
                    branches: ["branch2"],
                    timestamp: "2023-10-21T11:33:55Z",
                    parent_oid: "ghi789",
                    nb_parent_oid: "abc123",
                    tags: [],
                    code_version: "v1.0",
                    varset_version: "v0.9",
                    message: "Auto-commit after executing some changes",
                }
            ],
            head: {
                commit_id: "abc123",
                branch_name: "main"
            },
            nb_head: "ghi789"
        };

        fetchMock.get(`${BACKEND_URL}/api/fe/commit_graph?notebook_path=some_notebook_path`, {
            status: 200,
            body: mockResponse,
        });

        const result = await BackEndAPI.getCommitGraph();
        expect(result).toEqual(parseCommitGraph(mockResponse));
    });

    it("should throw error if getCommitGraph fails", async () => {
        fetchMock.get(`${BACKEND_URL}/api/fe/commit_graph?notebook_path=some_notebook_path`, 500);

        await expect(BackEndAPI.getCommitGraph()).rejects.toThrow("get commit graph backend error, status != 200");
    });

    it("should parse commit detail correctly", async () => {
        const mockResponse = {
            commit: {
                oid: "abc123",
                code_version: "v2.0",
                variable_version: "v1.1",
                timestamp: "2023-10-22T12:34:56Z",
                parent_oid: "def456",
                nb_parent_oid: "ghi789",
                branches: ["branch1", "branch2"],
                tags: ["v1.0", "v1.1"],
                message: "Fixed a bug and updated variables",
            },
            cells: [
                {
                    content: "print('Hello World')",
                    exec_num: "1",
                    cell_type: "code",
                    output: "Hello World\n"
                },
                {
                    content: "x = 10",
                    exec_num: "2",
                    cell_type: "code",
                    output: ""
                }
            ],
            variables: [
                {
                    name: "x",
                    type: "int",
                    state: "10"
                },
                {
                    name: "module1",
                    type: "module",
                    state: "<module 'module1' from '/path/to/module1.py'>"
                }
            ],
            executed_cells: [
                "print('Hello World')",
                "x = 10"
            ],
            executed_outputs: {
                "0": "Hello World\n",
                "1": ""
            }
        };

        fetchMock.get(`${BACKEND_URL}/api/fe/commit?notebook_path=some_notebook_path&commit_id=123`, {
            status: 200,
            body: mockResponse,
        });

        const result = await BackEndAPI.getCommitDetail("123");
        expect(result).toEqual(parseCommitDetail(mockResponse));
    });

    it("should throw error if getCommitDetail fails", async () => {
        fetchMock.get(`${BACKEND_URL}/api/fe/commit?notebook_path=some_notebook_path&commit_id=123`, 500);

        await expect(BackEndAPI.getCommitDetail("123")).rejects.toThrow("get commit detail error, status != 200");
    });

    it("should call setTag and deleteTag successfully", async () => {
        fetchMock.get(`${BACKEND_URL}/api/delete_tag?notebook_path=some_notebook_path&tag_name=oldTag`, 200);
        fetchMock.get(`${BACKEND_URL}/api/tag?notebook_path=some_notebook_path&commit_id=123&tag_name=newTag`, 200);

        await expect(BackEndAPI.setTag("123", "newTag", "oldTag")).resolves.toBeUndefined();
        expect(fetchMock.calls()).toHaveLength(2);
    });

    it("should throw error if deleteTag fails", async () => {
        fetchMock.get(`${BACKEND_URL}/api/delete_tag?notebook_path=some_notebook_path&tag_name=oldTag`, 500);

        await expect(BackEndAPI.setTag("123", "newTag", "oldTag")).rejects.toThrow("delete tags error, status != 200");
    });

    it("should call setMessage successfully", async () => {
        fetchMock.get(`${BACKEND_URL}/api/fe/edit_message?notebook_path=some_notebook_path&commit_id=123&new_message=newMessage`, 200);

        await expect(BackEndAPI.setMessage("123", "newMessage")).resolves.toBeUndefined();
        expect(fetchMock.calls()).toHaveLength(1);
    });

    it("should throw error if setMessage fails", async () => {
        fetchMock.get(`${BACKEND_URL}/api/fe/edit_message?notebook_path=some_notebook_path&commit_id=123&new_message=newMessage`, 500);

        await expect(BackEndAPI.setMessage("123", "newMessage")).rejects.toThrow("setting message error, status != 200");
    });

    // Add more tests for the other functions like getCodeDiff, getDataDiff, etc.

});
