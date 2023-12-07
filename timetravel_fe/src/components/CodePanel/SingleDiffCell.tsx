import AceEditor, {IMarker} from "react-ace";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import "ace-builds/src-noconflict/ext-language_tools";
import "./Cell.css";
import {DiffHunk} from "../../util/DiffHunk";
import {useEffect, useMemo, useRef, useState} from "react";
import "ace-builds"
import {Range} from "ace-builds";


export interface SingleDiffCellProps {
    diffHunk: DiffHunk
    cssClassNames?: string;
}

//helper functions
function countLines(text: string) {
    const lines = text.split("\n");
    return lines.length;
}

function updateMarkers(diffHunk:DiffHunk, setMarkers:any) {
    if (diffHunk.option === "Origin_only") {
        setMarkers([{
            startRow: 0,
            startCol: 0,
            endRow: countLines(diffHunk.content) - 1,
            endCol: 4,
            type: "fullLine",
            className: "delete-row-marker"
        }])
    } else if (diffHunk.option === "Destination_only") {
        setMarkers([{
            startRow: 0,
            startCol: 0,
            endRow: countLines(diffHunk.content) - 1,
            endCol: 4,
            type: "fullLine",
            className: "add-row-marker"
        }])
    } else if (diffHunk.option === "Both" && diffHunk.subDiffHunks) {
        setMarkers(diffHunk.subDiffHunks.map((subhunk, i) => {
            if (subhunk.option === "Origin_only") {
                return {
                    startRow: i,
                    startCol: 0,
                    endRow: i,
                    endCol: 4,
                    type: "fullLine",
                    className: "delete-row-marker"
                }
            } else if (subhunk.option === "Destination_only") {
                return {
                    startRow: i,
                    startCol: 0,
                    endRow: i,
                    endCol: 4,
                    type: "fullLine",
                    className: "add-row-marker"
                }
            } else {
                return undefined//no marker
            }
        }).filter(marker => marker !== undefined) as IMarker[]);
    } else {
        setMarkers(undefined)
    }

}

function updateContent(diffHunk:DiffHunk,setContent:any) {
    if (diffHunk.option === "Origin_only") {
        setContent(diffHunk.content)
    } else if (diffHunk.option === "Destination_only") {
        setContent(diffHunk.content)
    } else if (diffHunk.option === "Both" && diffHunk.subDiffHunks) {
        setContent(diffHunk.subDiffHunks.map((subhunk) => {
            return subhunk.content
        }).join("\n"))
    } else {
        setContent(diffHunk.content)
    }
}

function clearMarkers(ref: React.MutableRefObject<AceEditor | null>) {
    if (ref.current) {
        let editor = ref.current.editor
        const prevMarkers = editor.session.getMarkers();
        if (prevMarkers) {
            const prevMarkersArr = Object.keys(prevMarkers);
            for (let item of prevMarkersArr) {
                editor.session.removeMarker(prevMarkers[Number(item)].id);
            }
        }
    }
}

function addMarkers(ref: React.MutableRefObject<AceEditor | null>,markers:IMarker[]|undefined) {
    if (markers !== undefined && ref.current) {
        markers.forEach(
            ({
                 startRow,
                 startCol,
                 endRow,
                 endCol,
                 className,
                 type,
                 inFront = false
             }) => {
                const range = new Range(startRow, startCol, endRow, endCol);
                ref.current!.editor.session.addMarker(range, className, type, inFront);
            })
    }
}

function SingleDiffCell(props: SingleDiffCellProps) {
    const [content, setContent] = useState<string>("");
    const aceRef = useRef<AceEditor | null>(null);
    const [markers, setMarkers] = useState<IMarker[] | undefined>(undefined);



    useMemo(() => {
        // update the states
        updateContent(props.diffHunk, setContent)
        updateMarkers(props.diffHunk, setMarkers)
    }, [props.diffHunk])

    useEffect(() => {
        // manually update the markers because there are logical bugs in react-ace
        clearMarkers(aceRef)
        addMarkers(aceRef,markers)
    }, [props.diffHunk,markers]);


    return (
        <div className="singleCellLayout">
            <AceEditor
                // key = {objectHash(props.diffHunk)}
                ref={aceRef}
                className={"cell-code"}
                // className={!props.execNumber ? "code unexcecuted" : "code executed"}
                placeholder="Placeholder Text"
                mode="python"
                theme="github"
                name="blah2"
                fontSize={14}
                width="100%"
                height={(countLines(content) * 20).toString() + "px"}
                // height="10px"
                showPrintMargin={false}
                showGutter={false}
                highlightActiveLine={false}
                value={content}
                readOnly
                setOptions={{
                    enableBasicAutocompletion: false,
                    enableLiveAutocompletion: false,
                    enableSnippets: false,
                    showLineNumbers: true,
                    useWorker: false,
                    tabSize: 2,
                }}
            />
        </div>
    );
}

export default SingleDiffCell;
