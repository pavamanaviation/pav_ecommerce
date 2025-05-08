import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./AddCategory.css";
import UploadFileIcon from "../../assets/images/upload-file-icon.svg";
import SuccessIcon from "../../assets/images/succes-icon.png";
import SuccessMessageImage from "../../assets/images/success-message.svg";

const AddCategory = () => {
  const [name, setName] = useState(""); 
  const [image, setImage] = useState(null); 
  const [imagePreview, setImagePreview] = useState(null); 
  const [isImageUploaded, setIsImageUploaded] = useState(false); 
  const [loading, setLoading] = useState(false); 
  const [successMessage, setSuccessMessage] = useState("");
  const navigate = useNavigate(); 

  // Check session validity when component loads
  useEffect(() => {
    const adminId = sessionStorage.getItem("admin_id");

    if (!adminId) {
      alert("Session expired. Please log in again.");
      sessionStorage.clear();
      navigate("/admin-login");
    }
  }, [navigate]);

  // Success message handler
  const showSuccessMessage = (message) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  // Handle file selection
  const handleFileChange = (e) => {
    if (e.target.files.length === 0) return;
    const file = e.target.files[0];

    setImage(file);
    setImagePreview(URL.createObjectURL(file));
    setIsImageUploaded(true);

    e.target.value = ""; 
  };

  // Handle category submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    const adminId = sessionStorage.getItem("admin_id");

    if (!adminId) {
      alert("Admin session expired. Please log in again.");
      navigate("/admin-login");
      return;
    }

    if (!name.trim()) {
      alert("Please enter the category name.");
      return;
    }
    if (!image) {
      alert("Please upload an image.");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("admin_id", adminId); // Ensure correct admin ID
    formData.append("category_name", name);
    formData.append("category_image", image);

    try {
      const response = await fetch("http://65.0.183.78:8000/add-category", {
        method: "POST",
        body: formData,
        headers: {
          "Accept": "application/json",
        },
      });

      const data = await response.json();
      if (response.ok) {
        showSuccessMessage("Category added successfully!");
        navigate("/view-categories", { state: { successMessage: "Category added successfully!" } });
      } else {
        alert(data.error || "Failed to add category.");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Handle cancel button
  const handleCancel = () => {
    navigate("/view-categories"); 
  };

  return (
    <div className="add-card-form-page">
      <header className="form-header">
        <h1 className="form-title">Category Details</h1>
        {successMessage && (
          <div className="success-message-container">
            <img src={SuccessMessageImage} alt="Success" className="success-image" />
            <p className="success-message-text">{successMessage}</p>
          </div>
        )}
      </header>
      <div className="add-card-form">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name" className="category-name-label">
              Name of the Category
            </label>
            <input
              type="text"
              id="name"
              className="category-name-input"
              placeholder="Enter the Category Name..."
              value={name}
              onChange={(e) => setName(e.target.value)} 
            />
          </div>

          <div className="form-group upload-file">
            <label htmlFor="image" className="upload-label">
              Upload an Image
            </label>
            <div
              className="upload-box"
              onClick={(e) => {
                e.stopPropagation(); 
                document.getElementById("image").click(); 
              }}
            >
              {isImageUploaded ? (
                <div className="success-icon">
                  <img src={SuccessIcon} alt="Success Icon" className="success-icon-img" />
                  <p>Successfully uploaded file</p>
                </div>
              ) : (
                <>
                  <img src={UploadFileIcon} alt="Upload Icon" className="upload-icon" />
                  <p className="upload-text">
                    <span>Upload File</span> or Drag and Drop
                  </p>
                  {/* <p className="upload-text-mb">Up to 20MB</p> */}
                </>
              )}
              <input
                type="file"
                id="image"
                className="upload-input"
                onChange={handleFileChange} 
                onClick={(e) => e.stopPropagation()} 
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="button" onClick={handleCancel} className="admin-cancel-button">
              Cancel
            </button>
            <button type="submit" className="admin-submit-button" disabled={loading}>
              {loading ? "Submitting..." : "Submit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddCategory;