import React, { useEffect } from "react";
import { FaTimesCircle } from "react-icons/fa";
import "../Popup/Popup.css";

const PopupMessage = ({ message, type, onClose }) => {
    useEffect(() => {
        const timer = setTimeout(onClose, 10000); // Auto-close after 10 seconds
        return () => clearTimeout(timer);
    }, [onClose]);

    if (!message) return null; // Don't render if no message

    return (
        <div className={`popup-message ${type}`}>
            <span className="popup-text">{message}</span>
            <FaTimesCircle className="popup-close-btn" onClick={onClose} />
        </div>
    );
};

export default PopupMessage;
