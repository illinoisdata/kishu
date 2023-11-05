// // src/components/Menu.tsx
// import React from 'react';
//
// interface MenuItem {
//     label: string;
//     url: string;
// }
//
// interface MenuProps {
//     items: MenuItem[];
//     onItemClick: (url: string) => void;
// }
//
// const Menu: React.FC<MenuProps> = ({ items, onItemClick }) => {
//     return (
//         <ul>
//             {items.map((item) => (
//                 <li key={item.url} onClick={() => onItemClick(item.url)}>
//                     {item.label}
//                 </li>
//             ))}
//         </ul>
//     );
// };
//
// export default Menu;

// src/components/Menu.tsx
import React, {useEffect, useRef, useState} from 'react';
import "./Menu.css"
import {message, Select} from "antd";
import {BackEndAPI} from "./util/API";
import {Session} from "./util/Session";

function Menu() {
    const selectRef = useRef(null);
    const [sessions, setSessions] = useState<Session[]>([]);

    //get notebook names from backend
    useEffect(() => {
        //initialize the states
        async function getSessions() {
            try {
                const data = await BackEndAPI.getNotebookList()
                setSessions(data);
            } catch (e) {
                if (e instanceof Error) {
                    message.error(e.message);
                }
            }
        }

        getSessions();
    }, []);

    const handleChange = (value: string) => {
        const selectedPage = "/" + value
        if (selectedPage) {
            window.open(selectedPage, '_blank');
        }
    };

    return (
        <div className={"parent"}>
            <div className="d2">Welcome To Kishu</div>
            <Select
                open={true}
                ref={selectRef}
                showSearch
                style={{width: "80%", textAlign: "center"}}
                placeholder="select or search your notebook"
                optionFilterProp="children"
                filterOption={(input, option) => (option?.label ?? "").includes(input)}
                filterSort={(optionA, optionB) =>
                    (optionA?.label ?? "")
                        .toLowerCase()
                        .localeCompare((optionB?.label ?? "").toLowerCase())
                }
                onSelect={(value) => {
                    handleChange(value);
                }}
                options={sessions.map((session) => {
                    return {
                        value: session.NotebookID,
                        label: session.notebookPath
                    }
                })}
            />
        </div>)

};

export default Menu;
