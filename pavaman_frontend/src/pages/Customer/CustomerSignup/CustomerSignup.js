import React, { useState } from "react";
import "../CustomerSignup/CustomerSignup.css";
import Logo from "../../../assets/images/aviation-logo.png";
import LogInImage from "../../../assets/images/signinpage-image.png";
import { FaEye, FaEyeSlash, FaInfoCircle } from "react-icons/fa";
import PhoneInput from "react-phone-input-2";
import "react-phone-input-2/lib/style.css";
import { useNavigate } from "react-router-dom";
import PopupMessage from "../../../components/Popup/Popup";

const CustomerSignup = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        email: "",
        mobile_no: "",
        password: "",
        re_password: "",
    });

    const [showPassword, setShowPassword] = useState(false);
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showTooltip, setShowTooltip] = useState(false);

    const showPopup = (text, type) => {
        setPopupMessage({ text, type });
        setTimeout(() => setPopupMessage({ text: "", type: "" }), 10000);
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleMobileChange = (value) => {
        setFormData({ ...formData, mobile_no: value });
    };

    const validateEmail = (email) => /\S+@\S+\.\S+/.test(email);

    const validatePhoneNumber = (phone) => phone.length >= 10;

    const validatePassword = (password) => {
        const regex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$/;
        return regex.test(password);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateEmail(formData.email)) {
            showPopup("Invalid email format.", "error");
            return;
        }

        if (!validatePhoneNumber(formData.mobile_no)) {
            showPopup("Invalid mobile number.", "error");
            return;
        }

        if (!validatePassword(formData.password)) {
            showPopup("Password must be at least 8 characters long and contain both letters and numbers.", "error");
            return;
        }

        if (formData.password !== formData.re_password) {
            showPopup("Passwords must match.", "error");
            return;
        }

        try {
            const response = await fetch("http://65.0.183.78:8000/customer-register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                // body: JSON.stringify(formData),
                body: JSON.stringify({
                    ...formData,
                    mobile_no: formData.mobile_no.startsWith("+") ? formData.mobile_no : "+" + formData.mobile_no
                }),
                
            });

            const data = await response.json();

            if (response.ok) {
                showPopup("Signup successful! Verification link sent to your email.", "success");
                setFormData({
                    first_name: "",
                    last_name: "",
                    email: "",
                    mobile_no: "",
                    password: "",
                    re_password: "",
                });
                navigate("/customer-login", {
                    state: { successMessage: "Account created successfully! Please check your mail for verifying your account." }
                });
            } else if (data.status_code === 409) {
                showPopup(data.error, "error");
            } else {
                showPopup(data.error || "Signup failed.", "error");
            }
        } catch (error) {
            showPopup("Something went wrong. Please try again.", "error");
        }
    };

    return (
        <div className="signup-container">


            <div className="signup-form-section customer-signup-form">
                <img src={Logo} className="signup-logo" alt="Logo" />

                {/* <div>
                    <img src={Logo} className="signup-logo" alt="Logo" />
                </div> */}

                <div className="signup-text">Create Account</div>
                <div className="signup-form-fields">
                {popupMessage.text && (
                    <PopupMessage
                        message={popupMessage.text}
                        type={popupMessage.type}
                        onClose={() => setPopupMessage({ text: "", type: "" })}
                    />
                )}
                    <label className="signup-label">First Name <span className="required-star">*</span></label>
                    <input
                        type="text"
                        name="first_name"
                        className="signup-input-field"
                        placeholder="Enter your first name"
                        value={formData.first_name}
                        onChange={handleChange}
                        required
                    />
                </div>

                <div className="signup-form-fields">
                    <label className="signup-label">Last Name <span className="required-star">*</span></label>
                    <input
                        type="text"
                        name="last_name"
                        className="signup-input-field"
                        placeholder="Enter your last name"
                        value={formData.last_name}
                        onChange={handleChange}
                        required
                    />
                </div>

                <div className="signup-form-fields">
                    <label className="signup-label">Email <span className="required-star">*</span></label>
                    <input
                        type="email"
                        name="email"
                        className="signup-input-field"
                        placeholder="Enter your email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                    />
                </div>

                <div className="signup-form-fields">
                    <label className="signup-label">Mobile Number <span className="required-star">*</span></label>
                    <div className="signup-phone-input">
                        <PhoneInput
                            country={"in"}
                            value={formData.mobile_no}
                            onChange={handleMobileChange}
                            inputClass="signup-input-field signup-mobile"
                            containerClass="signup-phone-input"
                            required
                        />
                    </div>
                </div>

                <div className="signup-form-fields">
                    <label className="signup-label">Password
                        <span
                            className="password-tooltip-icon"
                            onMouseEnter={() => setShowTooltip(true)}
                            onMouseLeave={() => setShowTooltip(false)}

                        >
                            <span className="required-star">*</span>
                            <FaInfoCircle />
                        </span>
                    </label>
                    {showTooltip && (
                        <div className="password-tool-tip">
                            <ul className="password-tool-tip-list" >
                                <li>At least 8 characters long</li>
                                <li>Contains an uppercase letter</li>
                                <li>Contains a lowercase letter</li>
                                <li>Contains a special character</li>
                                <li>Contains a number</li>
                            </ul>
                        </div>
                    )}
                    <div className="signup-password-input-wrapper">
                        <input
                            type={showPassword ? "text" : "password"}
                            name="password"
                            className="signup-input-field signup-password-input"
                            placeholder="Enter your password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                        />
                        <span className="signup-password-toggle-btn" onClick={() => setShowPassword(!showPassword)}>
                            {showPassword ? <FaEyeSlash /> : <FaEye />}
                        </span>
                    </div>
                </div>

                <div className="signup-form-fields">
                    <label className="signup-label">Confirm Password<span className="required-star">*</span></label>
                    <div className="signup-password-input-wrapper">
                        <input
                            type={showPassword ? "text" : "password"}
                            name="re_password"
                            className="signup-input-field signup-password-input"
                            placeholder="Re-enter your password"
                            value={formData.re_password}
                            onChange={handleChange}
                            required
                        />
                        <span className="signup-password-toggle-btn" onClick={() => setShowPassword(!showPassword)}>
                            {showPassword ? <FaEyeSlash /> : <FaEye />}
                        </span>
                    </div>
                </div>

                <div className="signup-wrapper">
                    <button className="signup-btn" onClick={handleSubmit}>
                        <p className="signup-btn-text">Sign Up</p>
                    </button>
                    <button className="signup-btn" onClick={() => navigate("/customer-login")}>
                        <p className="signup-btn-text">Login </p>
                    </button>
                </div>
            </div>

            <div className="signup-image-section">
                <div className="signup-image-text">
                    “Power On with <span>Confidence.”</span>
                </div>
                <img className="signup-image" alt="Sign Up" src={LogInImage} />
            </div>
        </div>
    );
};

export default CustomerSignup;

