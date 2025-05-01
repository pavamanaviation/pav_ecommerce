// src/pages/Customer/CustomerViewAddress.js

import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import PopupMessage from "../../../components/Popup/Popup";
import "../CustomerViewOrder/CustomerViewOrder.css";

const CustomerViewOrder = () => {
  const [popupMessage, setPopupMessage] = useState("");
  const [popupType, setPopupType] = useState("success");
  const [showPopup, setShowPopup] = useState(false);
  const navigate = useNavigate();

  const displayPopup = (message, type = "success") => {
    setPopupMessage(message);
    setPopupType(type);
    setShowPopup(true);
  };

  const handleClosePopup = () => {
    setShowPopup(false);
    setPopupMessage("");
    setPopupType("success");
  };

  const fetchOrderDetails = async () => {
    const customer_id = localStorage.getItem("customer_id");

    if (!customer_id) {
      displayPopup(
        <>
          Please{" "}
          <Link to="/customer-login" className="popup-link">
            log in
          </Link>{" "}
          to view your orders.
        </>,
        "error"
      );
      return;
    }

    // Add your actual order-fetch logic here
  };

  useEffect(() => {
    fetchOrderDetails();
  }, []);

  return (
    <div className="customer-view-order container">
        <div className="order-popup">

      {showPopup && (
        <PopupMessage
          message={popupMessage}
          type={popupType}
          onClose={handleClosePopup}
        />
      )}
        </div>
    </div>
  );
};

export default CustomerViewOrder;
 