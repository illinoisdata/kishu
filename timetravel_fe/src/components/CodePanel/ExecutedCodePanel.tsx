/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 22:14:31
 * @LastEditTime: 2023-07-18 11:46:05
 * @FilePath: /src/components/CodePanel/ExecutedCodePanel.tsx
 * @Description: The panel to display code cells of the currently selected history
 */
import { useContext, useEffect, useLayoutEffect, useRef } from "react";
import { AppContext } from "../../App";
import SingleCell from "./SingleCell";

// export interface CodePanelProps {
//   containerRef: React.MutableRefObject<HTMLDivElement | null>;
// }

function ExecutedCodePanel() {
  const props = useContext(AppContext);

  let containerRef = useRef<null | HTMLDivElement>(null);
  let targetRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to the element when the component mounts (for example, after data loads)
    if (containerRef.current && targetRef.current) {
      // containerRef.current.scrollTop = containerRef.current.scrollHeight;

      const container = containerRef.current;
      const target = targetRef.current;

      // Calculate the scroll position to bring the target element into view
      const scrollPosition = target.offsetTop - container.offsetTop;

      // Scroll to the target element
      container.scrollTop = scrollPosition;
    }
  }, [props]);

  const length = props!.selectedCommit!.historyExecCells.length;

  return (
    <div ref={containerRef}>
      {props!.selectedCommit!.historyExecCells.map((code, i) => (
        <div ref={i !== length - 1 ? null : targetRef} key={i}>
          <SingleCell execNumber={(i + 1).toString()} content={code.content} />
          <br />
        </div>
      ))}
    </div>
  );
}

export default ExecutedCodePanel;
