import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import UploadFileIcon from "../../assets/images/upload-file-icon.svg";
import SuccessIcon from "../../assets/images/succes-icon.png";
import "../EditSubCategory/EditSubCategory.css";


const EditSubcategory = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    subcategory_id,
    subcategory_name: initialSubcategoryName,
    category_id,
    category_name,
    subcategory_image,
  } = location.state || {};

  const [subcategoryName, setSubcategoryName] = useState(initialSubcategoryName);
  const [selectedImage, setSelectedImage] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    setSelectedImage(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const adminId = sessionStorage.getItem("admin_id");


    if (!adminId) {
      setError("Admin session expired. Please log in again.");
      navigate("/admin-login");
      return;
    }

    const formData = new FormData();
    formData.append("subcategory_id", subcategory_id);
    formData.append("subcategory_name", subcategoryName);
    formData.append("category_id", category_id);
    formData.append("admin_id", adminId);
    if (selectedImage) {
      formData.append("sub_category_image", selectedImage);
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/edit-subcategory", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        // alert("Subcategory updated successfully!");
        navigate("/view-subcategories", { state: { category_id, category_name,successMessage: "Subcategory updated successfully!"  } });
      } else {
        setError(data.error || "Failed to update subcategory.");
      }
    } catch (error) {
      setError("An error occurred. Please try again.");
    }
  };

  return (
    <div className="edit-sub-form-page">
      <header className="form-header">
        <h1 className="form-title">Edit SubCategory</h1>
       
      </header>

      {error && <p className="text-red-500 text-center">{error}</p>}
      <div className="add-card-form">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
        <label htmlFor="name" className="category-name-label">Category Name</label>
          <input type="text" value={category_name} readOnly  className="category-name-input  category-name" />
        </div>

        <div className="form-group edit-sub-form">
          <label htmlFor="name" className="category-name-label">Subcategory Name</label>
          <input
            type="text"
            value={subcategoryName}
            onChange={(e) => setSubcategoryName(e.target.value)}
            required
       className="category-name-input"
          />
        </div>

        {/* File Upload Field */}
        <div className="form-group upload-file edit-upload-file">
          <label  htmlFor="image" className="upload-label">Upload an Image</label>
          <div
            className="upload-box"
            onClick={(e) => {
              e.stopPropagation();
              document.getElementById("subcategory_image").click();
            }}
          >
            {selectedImage ? (
              <div className="success-icon">
                <img src={SuccessIcon} alt="Success Icon" className="success-icon-img" />
                <p>Successfully uploaded Image</p>
              </div>
            ) : (
              <>
                <img src={UploadFileIcon} alt="Upload Icon" className="upload-icon" />
                <p className="upload-text">
                  <span>Upload File</span> or Drag and Drop
                </p>
                <p className="upload-text-mb">Up to 20MB</p>
              </>
            )}
            <input
              type="file"
              id="subcategory_image"
              name="subcategory_image"
              className="upload-input"
              onChange={handleFileChange}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="form-actions">
          <button type="button" onClick={() => navigate(-1)} className="admin-cancel-button">
            Cancel
          </button>
          <button type="submit"  className="admin-submit-button">
            Update 
          </button>
        </div>
      </form>
    </div>
    </div>
  );
};

export default EditSubcategory;
