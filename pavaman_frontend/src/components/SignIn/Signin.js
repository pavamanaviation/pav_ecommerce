import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "../SignIn/Signin.css";
import Logo from "../../assets/images/aviation-logo.png";
import LogInImage from "../../assets/images/signinpage-image.png";
import { FaEye, FaEyeSlash } from "react-icons/fa";

const SignIn = ({ setIsAuthenticated }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
  const navigate = useNavigate();
  const [isOtpStep, setIsOtpStep] = useState(false);
  const [otp, setOtp] = useState("");
  const [adminId, setAdminId] = useState(null);
  const [adminEmail, setAdminEmail] = useState("");

  const showPopup = (text, type) => {
    setPopupMessage({ text, type });
    setTimeout(() => {
      setPopupMessage({ text: "", type: "" });
    }, 3000);
  };

  const handleSignIn = async () => {
    if (!email || !password) {
      showPopup("Email and password are required.", "error");
      return;
    }

    try {
      const response = await axios.post("http://65.0.183.78:8000/admin-login", {
        email,
        password,
      });

      if (response.data.status_code === 200) {
        setAdminEmail(email);
        setIsOtpStep(true); // Show OTP popup
        showPopup("OTP sent to your registered mobile number", "success");
      } else {
        showPopup(response.data.error || "Login failed.", "error");
      }
    } catch (error) {
      showPopup(
        error.response?.data?.error || "Something went wrong.",
        "error"
      );
    }
  };

  const handleVerifyOtp = async () => {
    if (!otp) {
      showPopup("Please enter the OTP.", "error");
      return;
    }
  
    try {
      const verifyResponse = await axios.post(
        "http://65.0.183.78:8000/admin-verify-otp",
        {
          email: adminEmail,
          otp,
        }
      );
  
      const { status_code, error, id } = verifyResponse.data;
  
      if (status_code === 200) {
        showPopup("OTP Verified Successfully!", "success");
        setIsAuthenticated(true);
  
        sessionStorage.setItem("adminData", JSON.stringify(verifyResponse.data));
        sessionStorage.setItem("admin_id", id);
        navigate("/admin/dashboard");
      } else {
        // Handles invalid OTP or other backend errors
        const errorMessage = error || "OTP verification failed.";
        showPopup(errorMessage, "error");
        setOtp(""); // clear OTP field

      }
    } catch (err) {
      // Handles network or unexpected errors
      const message =
        err.response?.data?.error || "Something went wrong during OTP verification.";
      showPopup(message, "error");
      setOtp(""); // clear OTP field

    }
  };
  


  return (
    <div className="login-container">
      <div className="login-form-section">
        <div>
          <img src={Logo} className="login-logo" alt="Logo" />
        </div>

        <div className="login-text">Login</div>
        <div className="login-form-info">Fill the fields below to continue.</div>

        <div className="sign-in-popup">

          {popupMessage.text && (
            <div className={`popup-message ${popupMessage.type}`}>
              {popupMessage.text}
            </div>
          )}
        </div>

        <div className="login-form-fields">
          <label className="email-label">Email</label>
          <input
            type="email"
            className="login-input-field"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="login-form-fields">
          <label className="password-label">Password</label>
          <div className="password-input-wrapper">
            <input
              type={showPassword ? "text" : "password"}
              className="login-input-field password-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <span
              className="password-toggle-btn"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <FaEyeSlash /> : <FaEye />}
            </span>
          </div>
        </div>

        <div className="login-wrapper">
          <button className="login-btn" onClick={handleSignIn}>
            <p className="login-btn-text">Login</p>
          </button>
        </div>
      </div>

      <div className="login-image-section">
        <div className="image-text">
          “Power On with <span>Confidence.”</span>
        </div>
        <img className="login-image" alt="Sign In" src={LogInImage} />
      </div>

      {isOtpStep && (
        <div className="otp-popup">
          <div className="otp-popup-content">
            <div className="otp-popup-heading">Enter OTP</div>
            <div className="otp-popup-input-field">
              <input
                type="text"
                placeholder="Enter OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="otp-popup-input"
              />
            </div>
            <button onClick={handleVerifyOtp} className="otp-verify-btn">
              Verify
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SignIn;
