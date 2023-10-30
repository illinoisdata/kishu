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

function SingleDiffCell(props: SingleDiffCellProps) {
    const [content, setContent] = useState<string>("");
    const aceRef = useRef<AceEditor | null>(null);
    const [markers, setMarkers] = useState<IMarker[] | undefined>(undefined);

    function updateMarkers() {
        if (props.diffHunk.option == "Origin_only") {
            setMarkers([{
                startRow: 0,
                startCol: 0,
                endRow: countLines(props.diffHunk.content) - 1,
                endCol: 4,
                type: "fullLine",
                className: "delete-row-marker"
            }])
        } else if (props.diffHunk.option == "Destination_only") {
            setMarkers([{
                startRow: 0,
                startCol: 0,
                endRow: countLines(props.diffHunk.content) - 1,
                endCol: 4,
                type: "fullLine",
                className: "add-row-marker"
            }])
        } else if (props.diffHunk.option == "Both" && props.diffHunk.subDiffHunks) {
            setMarkers(props.diffHunk.subDiffHunks.map((subhunk, i) => {
                {
                    if (subhunk.option == "Origin_only") {
                        return {
                            startRow: i,
                            startCol: 0,
                            endRow: i,
                            endCol: 4,
                            type: "fullLine",
                            className: "delete-row-marker"
                        }
                    } else if (subhunk.option == "Destination_only") {
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
                }
            }).filter(marker => marker !== undefined) as IMarker[]);
        } else {
            setMarkers(undefined)
        }


        // }

    }

    function updateContent() {
        if (props.diffHunk.option == "Origin_only") {
            setContent(props.diffHunk.content)
        } else if (props.diffHunk.option == "Destination_only") {
            setContent(props.diffHunk.content)
        } else if (props.diffHunk.option == "Both" && props.diffHunk.subDiffHunks) {
            setContent(props.diffHunk.subDiffHunks.map((subhunk) => {
                return subhunk.content
            }).join("\n"))
        } else {
            setContent(props.diffHunk.content)
        }
    }

    function clearMarkers() {
        if (aceRef.current) {
            let editor = aceRef.current.editor
            const prevMarkers = editor.session.getMarkers();
            if (prevMarkers) {
                const prevMarkersArr = Object.keys(prevMarkers);
                for (let item of prevMarkersArr) {
                    editor.session.removeMarker(prevMarkers[Number(item)].id);
                }
            }
        }
    }

    function addMarkers() {
        if (markers != undefined && aceRef.current) {
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
                    aceRef.current!.editor.session.addMarker(range, className, type, inFront);
                })
        }
    }

    useMemo(() => {
        // update the states
        updateContent()
        updateMarkers()
    }, [props.diffHunk])

    useEffect(() => {
        // manually update the markers because there are logical bugs in react-ace
        clearMarkers()
        addMarkers()
    }, [props.diffHunk]);


    return (
        <div className="singleCellLayout">
            <AceEditor
                // key = {objectHash(props.diffHunk)}
                ref={aceRef}
                className={props.cssClassNames ? props.cssClassNames : "notebook"}
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
