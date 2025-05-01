import React, { useState } from "react";
import axios from "axios";
import { useLocation, useNavigate } from "react-router-dom";

const CustomerMobileVerification = () => {
    const [mobile, setMobile] = useState("");
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const location = useLocation();
    const navigate = useNavigate();
    // const userId = 1
    const userId = "17";

    console.log("User ID in Mobile Verification:", userId); // Debugging

    if (!userId) {
        navigate("/customer-login");
        return null;
    }

    const handleSubmitMobile = async () => {
        if (!mobile) {
            setPopupMessage({ text: "Mobile number is required.", type: "error" });
            return;
        }

        try {
            const response = await axios.post("http://127.0.0.1:8000/google-submit-mobile", {
                user_id: userId,
                mobile_no: mobile,
            });

            console.log("Submit Mobile Response:", response.data); // Debugging

            if (response.data.message) {
                setPopupMessage({ text: response.data.message, type: "success" });
                navigate("/");
            }
        } catch (error) {
            setPopupMessage({ text: error.response?.data?.error || "Mobile submission failed.", type: "error" });
        }
    };

    return (
        <div>
            <h2>Mobile Verification</h2>
            {popupMessage.text && <div className={popupMessage.type}>{popupMessage.text}</div>}
            <input
                type="text"
                placeholder="Enter your mobile number"
                value={mobile}
                onChange={(e) => setMobile(e.target.value)}
            />
            <button onClick={handleSubmitMobile}>Submit</button>
        </div>
    );
};

export default CustomerMobileVerification;
