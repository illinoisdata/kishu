/*
 * @Author: University of Illinois at Urbana Champaign
 * @Date: 2023-06-18 13:46:16
 * @LastEditTime: 2023-06-18 17:37:39
 * @FilePath: /src/components/HistoryPanel/HistoryTree.tsx
 * @Description:
 */
// import HistoryPoint from "../HistoryPoint";
import { Gitgraph } from "@gitgraph/react";

// const HistoryTree: React.FC = () => {
//   const handleNodeClick = (nodeLabel: string) => {
//     // Handle node click for the specific node
//     console.log(`Node clicked: ${nodeLabel}`);
//   };

//   const renderNodeWithLines = (node: React.ReactNode) => {
//     return (
//       <div>
//         <svg
//           width="100%"
//           height="100%"
//           style={{ position: "absolute", zIndex: -1 }}
//         >
//           {node}
//         </svg>
//         {node}
//       </div>
//     );
//   };

//   return (
//     <div style={{ position: "relative" }}>
//       {renderNodeWithLines(
//         <HistoryPoint label="Node 1" onClick={() => handleNodeClick("Node 1")}>
//           {renderNodeWithLines(
//             <HistoryPoint
//               label="Node 1.1"
//               onClick={() => handleNodeClick("Node 1.1")}
//             >
//               <HistoryPoint
//                 label="Node 1.1.1"
//                 onClick={() => handleNodeClick("Node 1.1.1")}
//               />
//               <HistoryPoint
//                 label="Node 1.1.2"
//                 onClick={() => handleNodeClick("Node 1.1.2")}
//               />
//             </HistoryPoint>
//           )}
//           <HistoryPoint
//             label="Node 1.2"
//             onClick={() => handleNodeClick("Node 1.2")}
//           />
//         </HistoryPoint>
//       )}
//       {renderNodeWithLines(
//         <HistoryPoint label="Node 2" onClick={() => handleNodeClick("Node 2")}>
//           <HistoryPoint
//             label="Node 2.1"
//             onClick={() => handleNodeClick("Node 2.1")}
//           />
//         </HistoryPoint>
//       )}
//     </div>
//   );
// };

function HistoryTree() {
  return (
    <Gitgraph>
      {(gitgraph) => {
        // Simulate git commands with Gitgraph API.
        const master = gitgraph.branch("master");
        master.commit({
          subject: "Add tests",
          onMessageClick(commit) {
            alert(`Commit ${commit.hash} selected`);
          },
          onMouseOver(commit) {
            alert(`Commit ${commit.hash} over`);
          },
        });
        // master.commit(subject:"Initial commit", onMessageClick(commit) {
        //   alert(`Commit ${commit.hash} selected`);
        // })
        // master.commit("Initial commit");
        // onMessageClick(commit) {
        //   alert(`Commit ${commit.hash} selected`);
        // }

        const develop = master.branch("develop");
        develop.commit("Add TypeScript");

        const aFeature = develop.branch("a-feature");
        aFeature
          .commit("Make it work")
          .commit("Make it right")
          .commit("Make it fast");

        const bFeature = develop.branch("b-feature");
        bFeature
          .commit("Make it work")
          .commit("Make it right")
          .commit("Make it fast");
        const cFeature = develop.branch("c-feature");
        cFeature
          .commit("Make it work")
          .commit("Make it right")
          .commit("Make it fast");

        // develop.merge(aFeature);
        develop.commit("Prepare v1");
        develop.commit("Add TypeScript");
        develop.commit("Add TypeScript");
        develop.commit("Add TypeScript");
        develop.commit("Add TypeScript");
        develop.commit("Add TypeScript");
        develop.commit("Add TypeScript");
        develop.commit("Add TypeScript");
        develop.commit("Add TypeScript");
        develop.commit("Add TypeScript");

        // master.merge(develop).tag("v1.0.0");
      }}
    </Gitgraph>
  );
}

export default HistoryTree;
