
import React, { useState, useEffect, useRef } from "react";
import "../CustomerAddAddress/CustomerAddAddress.css";
import PopupMessage from "../../../components/Popup/Popup";

const AddCustomerAddress = ({ onAddressAdded }) => {
    const wrapperRef = useRef(null);

    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        mobile_number: "",
        alternate_mobile: "",
        pincode: "",
        locality: "",
        address: "",
        city: "",
        email: "",
        state: "",
        landmark: "",
        district: "",
        street: "",
        mandal: "",
        addressType: "home",
    });

    const [loading, setLoading] = useState(false);
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);
        setTimeout(() => setShowPopup(false), 10000);
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    // Auto fetch state/district/mandal from pincode
    useEffect(() => {
        const fetchLocationDetails = async () => {
            if (formData.pincode.length === 6) {
                try {
                    const response = await fetch(`https://api.postalpincode.in/pincode/${formData.pincode}`);
                    const result = await response.json();

                    if (result[0].Status === "Success") {
                        const postOffice = result[0].PostOffice[0];
                        setFormData(prev => ({
                            ...prev,
                            district: postOffice.District,
                            state: postOffice.State,
                            mandal: postOffice.Block,
                        }));
                    } else {
                        setFormData(prev => ({
                            ...prev,
                            district: "",
                            state: "",
                            mandal: ""
                        }));
                    }
                } catch (error) {
                    console.error("Failed to fetch pincode details:", error);
                }
            }
        };
        fetchLocationDetails();
    }, [formData.pincode]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const customer_id = localStorage.getItem("customer_id");
        if (!customer_id) {
            alert("Please log in to continue.");
            setLoading(false);
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/add-customer-address", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id, ...formData }),
            });

            const data = await response.json();
            if (data.status_code === 200) {
                displayPopup("Address added successfully!", "success");
                setTimeout(() => {
                    onAddressAdded();
                }, 3000);
            } else {
                displayPopup(data.error || "Failed to add address.", "error");
            }
        } catch (error) {
            displayPopup("An unexpected error occurred.", "error");
            console.error("API Error:", error);
        } finally {
            setLoading(false);
        }
    };

    // Close on outside click
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                onAddressAdded();
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [onAddressAdded]);

    return (
        <div className="fedit-address">
            <div className="popup-cart">
                {showPopup && (
                    <PopupMessage
                        message={popupMessage.text}
                        type={popupMessage.type}
                        onClose={() => setShowPopup(false)}
                    />
                )}
            </div>
            <div ref={wrapperRef}>
                <h3 className="manage-form-title">ADD A NEW ADDRESS</h3>
                <form onSubmit={handleSubmit} className="manage-address-form">
                    {/* First & Last Name */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>First Name<span className="required-star">*</span></label>
                            <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} required />
                        </div>
                        <div className="manage-input-group">
                            <label>Last Name<span className="required-star">*</span></label>
                            <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} required />
                        </div>
                    </div>

                    {/* Mobile Numbers */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>Mobile Number<span className="required-star">*</span></label>
                            <input type="text" name="mobile_number" value={formData.mobile_number} onChange={handleChange} required pattern="\d{10}" />
                        </div>
                        <div className="manage-input-group">
                            <label>Alternate Mobile</label>
                            <input type="text" name="alternate_mobile" value={formData.alternate_mobile} onChange={handleChange} />
                        </div>
                    </div>

                    {/* Email & Pincode */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>Email<span className="required-star">*</span></label>
                            <input type="email" name="email" value={formData.email} onChange={handleChange} required />
                        </div>
                        <div className="manage-input-group">
                            <label>Pincode<span className="required-star">*</span></label>
                            <input type="text" name="pincode" value={formData.pincode} onChange={handleChange} required pattern="\d{6}" />
                        </div>
                    </div>

                    {/* Address */}
                    <label className="address-label">Address<span className="required-star">*</span></label>
                    <textarea className="manage-address-input" name="street" value={formData.street} onChange={handleChange} required />

                    {/* City & State */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>District<span className="required-star">*</span></label>
                            <input type="text" name="district" value={formData.district} onChange={handleChange} required />
                        </div>
                        <div className="manage-input-group">
                            <label>State<span className="required-star">*</span></label>
                            <input type="text" name="state" value={formData.state} onChange={handleChange} required />
                        </div>
                    </div>

                    {/* Mandal */}
                    <div className="manage-input-group">
                        <label>Mandal<span className="required-star">*</span></label>
                        <input type="text" name="mandal" value={formData.mandal} onChange={handleChange} required />
                    </div>

                    {/* Landmark & Locality */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>Landmark</label>
                            <input type="text" name="landmark" value={formData.landmark} onChange={handleChange} />
                        </div>
                        <div className="manage-input-group">
                            <label>Locality<span className="required-star">*</span></label>
                            <input type="text" name="locality" value={formData.locality} onChange={handleChange} required />
                        </div>
                    </div>

                    {/* Address Type */}
                    <div className="edit-manage-address-type address-space">
                        <label>Address Type</label>
                        <label>
                            <input type="radio" name="addressType" value="home" checked={formData.addressType === "home"} onChange={handleChange} />
                            Home
                        </label>
                        <label>
                            <input type="radio" name="addressType" value="work" checked={formData.addressType === "work"} onChange={handleChange} />
                            Work (10AM–6PM)
                        </label>
                    </div>

                    {/* Buttons */}
                    <div className="cart-actions">
                        <button type="submit" className="cart-place-order" disabled={loading}>
                            {loading ? "Saving..." : "SAVE"}
                        </button>
                        <button type="button" className="cart-delete-selected" onClick={() => onAddressAdded()}>
                            CANCEL
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddCustomerAddress;


