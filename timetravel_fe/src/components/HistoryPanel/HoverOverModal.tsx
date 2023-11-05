import React from "react";

export interface HoverOverProps {
    x: number;
    y: number;
    timestamp: string;
}

function HoverPopup({x, y, timestamp}: HoverOverProps) {
    return (
        <>
            <div
                style={{
                    position: "fixed",
                    top: y,
                    left: x,
                    zIndex: 9999,
                }}
            >
                {timestamp}
            </div>
        </>
    );
}

export default HoverPopup;
