import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./CustomerEditProfile.css";
import PopupMessage from "../../../components/Popup/Popup";

const CustomerEditProfile = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const customerData = location.state?.customer;

    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);
        setTimeout(() => {
            setShowPopup(false);
        }, 10000);
    };

    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        email: "",
        mobile_no: ""
    });

    useEffect(() => {
        if (customerData) {
            setFormData({
                first_name: customerData.first_name || "",
                last_name: customerData.last_name || "",
                email: customerData.email || "",
                mobile_no: customerData.mobile_no || ""
            });
        }
    }, [customerData]);

    if (!customerData) {
        return <div className="edit-profile-container"><p>Loading customer data...</p></div>;
    }

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch("http://127.0.0.1:8000/edit-customer-profile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    customer_id: localStorage.getItem("customer_id"),
                    ...formData
                }),
            });

            const result = await response.json();

            if (response.ok) {
                displayPopup("Profile updated successfully!", "success");
                setTimeout(() => navigate("/profile"), 3000);
            } else {
                displayPopup(result.error || "Failed to update profile", "error");
            }
        } catch (error) {
            displayPopup("Error updating profile: " + error.message, "error");
        }
    };

    return (
        <div className="edit-profile-container">
            {showPopup && (
                <div className="profile-popup-discount">
                    <PopupMessage
                        message={popupMessage.text}
                        type={popupMessage.type}
                        onClose={() => setShowPopup(false)}
                    />
                </div>
            )}

            <h2>Edit Your Profile</h2>

            <form onSubmit={handleSubmit} className="edit-profile-form">
                <div className="input-row">
                    <div className="input-single">
                        <h3 className="profile-edit-heading-first">First Name</h3>
                        <input
                            type="text"
                            name="first_name"
                            value={formData.first_name}
                            onChange={handleChange}
                            className="Customer-input-row-edit-profile"
                            required
                        />
                    </div>
                    <div className="input-single">
                        <h3 className="profile-edit-heading-first">Last Name</h3>
                        <input
                            type="text"
                            name="last_name"
                            value={formData.last_name}
                            onChange={handleChange}
                            className="Customer-input-row-edit-profile"
                            required
                        />
                    </div>
                </div>
                <div className="input-single">
                    <h3 className="profile-edit-heading-first">Email</h3>
                    <input
                        className="Customer-input-row-edit-profile"
                        type="email"
                        name="email"
                        id="email"
                        placeholder="Email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                    />
                </div>

                <div className="input-single">
                    <h3 className="profile-edit-heading-first">Mobile Number</h3>
                    <input
                        className="Customer-input-row-edit-profile"
                        type="text"
                        name="mobile_no"
                        id="mobile_no"
                        placeholder="Mobile Number"
                        value={formData.mobile_no}
                        onChange={handleChange}
                        pattern="\d{10}"
                        title="Mobile number must be exactly 10 digits"
                        required
                    />
                </div>

                <div className="button-row">
                    <button className="save-changes-edit-profile" type="submit">Save Changes</button>
                    <button className="cancel-edit-profile" type="button" onClick={() => navigate("/profile")}>Cancel</button>
                </div>
            </form>
        </div>
    );
};

export default CustomerEditProfile;

