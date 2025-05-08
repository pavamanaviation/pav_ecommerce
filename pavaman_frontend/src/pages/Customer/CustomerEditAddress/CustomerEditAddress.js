import React, { useState, useRef, useEffect } from "react";
import "./CustomerEditAddress.css";
import PopupMessage from "../../../components/Popup/Popup";
import PhoneInput from "react-phone-input-2";

const CartEditAddress = ({ address, onEditCompleted }) => {
    const wrapperRef = useRef(null);

    const [formData, setFormData] = useState({
        address_id: address.address_id,
        customer_id: localStorage.getItem("customer_id"),
        first_name: address.first_name || "",
        last_name: address.last_name || "",
        email: address.email || "",
        mobile_number: address.mobile_number || "",
        alternate_mobile: address.alternate_mobile || "",
        address_type: address.address_type || "home",
        pincode: address.pincode || "",
        street: address.street || "",
        landmark: address.landmark || "",
        latitude: address.latitude || "",
        longitude: address.longitude || "",
        state: address.state || "",
        district: address.district || "",
        mandal: address.mandal || ""
    });

    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);
    const [loading, setLoading] = useState(false);
    const customer_id = localStorage.getItem("customer_id");

    // Close when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                onEditCompleted(""); // Call cancel logic
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [onEditCompleted]);

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);
        setTimeout(() => setShowPopup(false), 10000);
    };

    const fetchLocationDetails = async (pincode) => {
        setLoading(true);
        try {
            const response = await fetch(`https://api.postalpincode.in/pincode/${pincode}`);
            const data = await response.json();
            if (data && data[0]?.Status === "Success" && data[0]?.PostOffice?.length > 0) {
                const postOfficeData = data[0].PostOffice[0];
                setFormData((prev) => ({
                    ...prev,
                    state: postOfficeData.State || "",
                    district: postOfficeData.District || "",
                    mandal: postOfficeData.Block || ""
                }));
            } else {
                displayPopup(data.error || "Failed to fetch location details.", "error");
            }
        } catch (error) {
            displayPopup("An unexpected error occurred while fetching location details.", "error");
            console.error("Location fetch error:", error);
        }
        setLoading(false);
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value
        }));
        if (name === "pincode" && /^[0-9]{6}$/.test(value)) {
            fetchLocationDetails(value);
        }
    };
    const handlePhoneChange = (value, name) => {
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch("http://65.0.183.78:8000/edit-customer-address", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id,...formData, mobile_number: `+${formData.mobile_number}`, alternate_mobile: formData.alternate_mobile ? `+${formData.alternate_mobile}` : "" })
            });

            const data = await response.json();
            if (response.ok) {
                displayPopup("Address updated successfully!", "success");
                onEditCompleted("Address updated successfully!");
            } else {
                displayPopup(data.error || "Failed to update address.", "error");
                onEditCompleted(data.error || "Failed to update address.");
            }
        } catch (error) {
            displayPopup("An unexpected error occurred.", "error");
            onEditCompleted("An unexpected error occurred.");
            console.error("Update error:", error);
        }
    };

    return (
        <div className="edit-address-overlay">
            <div className="edit-address" ref={wrapperRef}>
                <h3 className="form-title">Edit Address</h3>
                <div className="popup-cart">
                    {showPopup && (
                        <PopupMessage
                            message={popupMessage.text}
                            type={popupMessage.type}
                            onClose={() => setShowPopup(false)}
                        />
                    )}
                </div>
                <form onSubmit={handleSubmit} className="form-grid">
                    <div className="form-row">
                        <div className="input-group">
                            <input
                                className="input-text-field"
                                type="text"
                                name="first_name"
                                value={formData.first_name}
                                onChange={handleChange}
                                required
                            />
                            <label>First Name <span className="required-star">*</span></label>
                        </div>
                        <div className="input-group">
                            <input
                                className="input-text-field"
                                type="text"
                                name="last_name"
                                value={formData.last_name}
                                onChange={handleChange}
                                required
                            />
                            <label>Last Name <span className="required-star">*</span></label>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="input-group">
                            {/* <input
                                className="input-text-field"
                                type="text"
                                name="mobile_number"
                                value={formData.mobile_number}
                                onChange={handleChange}
                                required
                            /> */}

                        <label>Mobile Number <span className="required-star">*</span></label>
                            <PhoneInput
                                country={"in"}
                                value={formData.mobile_number}
                                onChange={(value) => handlePhoneChange(value, "mobile_number")}
                                inputProps={{ name: "mobile_number", required: true }}
                                // placeholder="Mobile Number"
                                required
                            />
                            {/* <label>Mobile Number <span className="required-star">*</span></label> */}
                        </div>
                        <div className="input-group">
                        <label>Alternate Mobile (Optional)</label>
                        <PhoneInput
                                country={"in"}
                                value={formData.alternate_mobile}
                                onChange={(value) => handlePhoneChange(value, "alternate_mobile")}
                                inputProps={{ name: "alternate_mobile" }}
                            />
                            {/* <label>Alternate Mobile (Optional)</label> */}
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="input-group">
                            <input
                                className="input-text-field"
                                type="text"
                                name="pincode"
                                value={formData.pincode}
                                onChange={handleChange}
                                required
                            />
                            <label>Pincode <span className="required-star">*</span></label>
                        </div>
                        <div className="input-group">
                            <input
                                className="input-text-field"
                                type="text"
                                name="state"
                                value={formData.state}
                                readOnly
                                required
                            />
                            <label>State <span className="required-star">*</span></label>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="input-group" style={{ width: "100%" }}>
                            <input className="input-text-field" type="text" name="mandal" value={formData.mandal || ""} onChange={handleChange} required />
                            <label>Mandal <span className="required-star">*</span></label>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="input-group" style={{ width: "100%" }}>
                            <input
                                className="input-text-field"
                                type="text"
                                name="street"
                                value={formData.street}
                                onChange={handleChange}
                                required
                            />
                            <label className="address-area">Address(Area, street, Flat No.) <span className="required-star">*</span></label>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="input-group">
                            <input
                                className="input-text-field"
                                type="text"
                                name="district"
                                value={formData.district}
                                readOnly
                                required
                            />
                            <label>District/Town <span className="required-star">*</span></label>
                        </div>
                        <div className="input-group">
                            <input
                                className="input-text-field"
                                type="text"
                                name="landmark"
                                value={formData.landmark}
                                onChange={handleChange}
                            />
                            <label>Landmark (Optional)</label>
                        </div>
                    </div>

                    <div className="form-row address-type-container" style={{ flexDirection: "column" }}>
                        <label className="Address-type">Address Type:</label>
                        <div className="address-type-options">
                            <div className="radio-option">
                                <input
                                    type="radio"
                                    id="home"
                                    name="address_type"
                                    value="home"
                                    checked={formData.address_type === "home"}
                                    onChange={handleChange}
                                />
                                <label htmlFor="home">Home</label>
                            </div>
                            <div className="radio-option">
                                <input
                                    type="radio"
                                    id="work"
                                    name="address_type"
                                    value="work"
                                    checked={formData.address_type === "work"}
                                    onChange={handleChange}
                                />
                                <label htmlFor="work">Work &nbsp;(10AM–6PM)</label>
                            </div>
                        </div>
                    </div>

                    <div className="cart-actions">
                        <button className="cart-place-order" type="submit">
                            SAVE
                        </button>
                        <button
                            className="cart-delete-selected"
                            type="button"
                            onClick={() => onEditCompleted("")}
                        >
                            CANCEL
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CartEditAddress;

