/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 22:14:31
 * @LastEditTime: 2023-07-18 11:46:05
 * @FilePath: /src/components/CodePanel/ExecutedCodePanel.tsx
 * @Description: The panel to display code cells of the currently selected history
 */
import { useContext, useEffect, useLayoutEffect, useRef } from "react";
import SingleCell from "./SingleCell";
import { AppContext } from "../../App";

export interface CodePanelProps {
  containerRef: React.MutableRefObject<HTMLDivElement | null>;
}

function CodePanel({ containerRef }: CodePanelProps) {
  const props = useContext(AppContext);

  // let targetRef = useRef<null | HTMLDivElement>(null);

  // useEffect(() => {
  //   // Scroll to the element when the component mounts (for example, after data loads)
  //   if (containerRef.current && targetRef.current) {
  //     // containerRef.current.scrollTop = containerRef.current.scrollHeight;
  //
  //     const container = containerRef.current;
  //     const target = targetRef.current;
  //
  //     // Calculate the scroll position to bring the target element into view
  //     const scrollPosition = target.offsetTop - container.offsetTop;
  //
  //     // Scroll to the target element
  //     container.scrollTop = scrollPosition;
  //   }
  // }, [props]);

  return (
    <div ref={containerRef}>
      {props!.selectedCommit!.codes!.map((code, i) => (
        <div
          // ref={
          //   code.execNum !== props!.selectedCommit!.execCell ? null : targetRef
          // }
          key={i}
        >
          <SingleCell execNumber={code.execNum} content={code.content} />
          <br />
        </div>
      ))}
    </div>
  );
}

export default CodePanel;
