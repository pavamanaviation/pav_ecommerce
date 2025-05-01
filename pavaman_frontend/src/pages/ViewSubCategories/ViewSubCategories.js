import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../ViewSubCategories/ViewSubCategories.css";
import AddIcon from "../../assets/images/addicon.svg";
import SuccessMessageImage from '../../../src/assets/images/success-message.svg';
import { FaEdit, FaTrash, FaTimes } from "react-icons/fa";
import { FaCircleCheck } from "react-icons/fa6";
import "react-toastify/dist/ReactToastify.css";
import "../ViewCategories/ViewCategories.css";

const ViewSubcategories = ({ subcategories, setSubcategories }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { category_id, category_name, successMessage: initialSuccessMessage } = location.state || {};
  const [successMessage, setSuccessMessage] = useState(initialSuccessMessage || "");
  
  const [showDeletePopup, setShowDeletePopup] = useState(false);
  const [subcategoryToDelete, setSubcategoryToDelete] = useState(null);
  const [showActionSuccessPopup, setShowActionSuccessPopup] = useState(!!successMessage);

  useEffect(() => {
    if (!category_id) {
      setError("Category ID is missing.");
      return;
    }
    fetchSubcategories();
  }, []);

  const fetchSubcategories = async () => {
    const adminId = sessionStorage.getItem("admin_id");

    if (!adminId) {
      setError("Admin session expired. Please log in again.");
      navigate("/admin-login");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/view-subcategories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin_id: adminId, category_id }),
      });

      const data = await response.json();
      if (response.ok) {
        setSubcategories(data.subcategories || []);
      } else {
        setError(data.error || "Something went wrong.");
      }
    } catch (error) {
      setError("Failed to fetch subcategories. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (subcategory) => {
    navigate("/edit-subcategory", {
      state: {
        subcategory_id: subcategory.id,
        subcategory_name: subcategory.sub_category_name,
        category_id: category_id,
        category_name: category_name,
        subcategory_image: subcategory.sub_category_image
      }
    });
  };

  const handleDelete = async () => {
    if (!subcategoryToDelete) return;

    const adminId = sessionStorage.getItem("admin_id");

    if (!adminId) {
      setError("Admin session expired. Please log in again.");
      navigate("/admin-login");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/delete-subcategory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          admin_id: adminId,
          category_id,
          subcategory_id: subcategoryToDelete,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        const deletedSubcategoryName = subcategories.find((sub) => sub.id === subcategoryToDelete)?.sub_category_name || "Subcategory";
        setSubcategories((prev) => prev.filter((item) => item.id !== subcategoryToDelete));
        setShowDeletePopup(false);
        setSuccessMessage(`${deletedSubcategoryName} deleted successfully!`);
        setShowActionSuccessPopup(true);
      } else {
        setError(data.error || "Failed to delete subcategory.");
      }
    } catch (error) {
      setError("Failed to delete subcategory. Please try again.");
    }
  };

  const handleAddSubcategory = () => {
    navigate("/add-subcategory", { state: { category_id, category_name } });
  };

  const handleViewProducts = (subcategory) => {
    sessionStorage.setItem("subCategoryData", JSON.stringify({

      sub_category_id: subcategory.id,
      sub_category_name: subcategory.sub_category_name
    }));
    const adminId = sessionStorage.getItem("admin_id");

    if (!adminId) {
      setError("Admin session expired. Please log in again.");
      navigate("/admin-login");
      return;
    }
    navigate("/view-products", {
      state: {
        sub_category_id: subcategory.id,
        sub_category_name: subcategory.sub_category_name,
        category_id: category_id,
        category_name: category_name
      }
    });
  };

  useEffect(() => {
    if (showActionSuccessPopup) {
      const timer = setTimeout(() => {
        setShowActionSuccessPopup(false);
        setSuccessMessage("");
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [showActionSuccessPopup]);

  return (
    <div>
      <div className="category-div">
        <div className="category-heading">Sub-Categories</div>

        {loading && <p className="loading">Loading...</p>}
        {error && <p className="error-message">{error}</p>}
        {!loading && subcategories.length === 0 && <p className="no-data">No subcategories found.</p>}
      </div>

      <div className="category-cards">
        {subcategories.map((subcategory) => (
          <div key={subcategory.id} className="category-card">
            <img src={subcategory.sub_category_image}
              alt={subcategory.sub_category_name}
              className="card-image"
              onClick={() => handleViewProducts(subcategory)} />
            <p className="card-name">{subcategory.sub_category_name}</p>
            <div className="card-menu">
              <div className="edit-label" onClick={() => handleEdit(subcategory)}>
                <FaEdit className="edit-icon" />
                <span className="card-menu-icon-label edit-label">Edit</span>
              </div>
              <div onClick={() => {
                setSubcategoryToDelete(subcategory.id);
                setShowDeletePopup(true);
              }} className="delete-label">
                <FaTrash className="delete-icon" />
                <span className="card-menu-icon-label delete-label">Delete</span>
              </div>
            </div>
          </div>
        ))}

        <div className="add-category-card" onClick={handleAddSubcategory}>
          <img src={AddIcon} alt="Add Subcategory" className="add-category-image" />
        </div>

        {showDeletePopup && (
          <div className="popup-overlay">
            <div className="popup-content">
              <p>
                Are you sure you want to delete{" "}
                <strong>
                  {subcategories.find((sub) => sub.id === subcategoryToDelete)?.sub_category_name || "this"}
                </strong>{" "}
                subcategory?
              </p>
              <div className="popup-buttons">
                <button className="popup-confirm" onClick={handleDelete}>Yes, Delete</button>
                <button className="popup-cancel" onClick={() => setShowDeletePopup(false)}>Cancel</button>
              </div>
            </div>
          </div>
        )}

        {showActionSuccessPopup && (
          <div className="popup-overlay">
            <div className="popup-content">
              <FaTimes className="popup-close-icon" onClick={() => setShowActionSuccessPopup(false)} />
              <div className="message">
                <FaCircleCheck className="success-icon" />
                <p className="success-message-text">{successMessage}</p>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default ViewSubcategories;
