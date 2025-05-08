import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import "../ViewProducts/ViewProducts.css";
import AddIcon from "../../assets/images/addicon.svg";
import { FaEdit, FaTrash, FaRupeeSign, FaTimes } from "react-icons/fa";
import { FaCircleCheck } from "react-icons/fa6";

const ViewProducts = ({ products, setProducts }) => {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const { sub_category_id, sub_category_name, category_id, category_name, successMessage } = location.state || {};
  const [message, setMessage] = useState(successMessage || "");

  const [showDeletePopup, setShowDeletePopup] = useState(false);
  const [productToDelete, setProductToDelete] = useState(null);
  const [productNameToDelete, setProductNameToDelete] = useState("");
  const [showActionSuccessPopup, setShowActionSuccessPopup] = useState(false);

  useEffect(() => {
    const adminId = sessionStorage.getItem("admin_id");


    if (!category_id || !sub_category_id) {
      setError("Category or Subcategory ID is missing.");
      setLoading(false);
      return;
    }

    fetchProducts(adminId);
  }, [navigate, category_id, sub_category_id]);

  useEffect(() => {
    if (successMessage) {
      setShowActionSuccessPopup(true);
    }
  }, [successMessage]);

  useEffect(() => {
    if (showActionSuccessPopup) {
      const timer = setTimeout(() => {
        setShowActionSuccessPopup(false);
        setMessage("");
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [showActionSuccessPopup]);

  const fetchProducts = async (adminId) => {
    try {
      const response = await axios.post("http://65.0.183.78:8000/view-products", {
        admin_id: adminId,
        category_id,
        sub_category_id,
      });

      if (response.data.status_code === 200) {
        setProducts(response.data.products || []);
      } else {
        setError(response.data.error || "Failed to fetch products.");
      }
    } catch (error) {
      setError("Error fetching products. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = () => {
    navigate("/add-product", {
      state: { category_id, category_name, sub_category_id, sub_category_name },
    });
  };

  const handleEditProduct = (product) => {
    navigate("/edit-product", {
      state: {
        category_id,
        category_name,
        sub_category_id,
        sub_category_name,
        product_id: product.product_id,
        product_name: product.product_name,
        sku_number: product.sku_number,
        price: product.price,
        quantity: product.quantity,
        discount: product.product_discount || "",
        description: product.product_description || "",
        product_images: product.product_images || [],
      },
    });
  };

  const handleDeleteProduct = async () => {
    const adminId = sessionStorage.getItem("admin_id");

    if (!adminId) {
      alert("Session expired. Please log in again.");
      navigate("/admin-login");
      return;
    }

    try {
      const response = await axios.post("http://65.0.183.78:8000/delete-product", {
        admin_id: adminId,
        category_id,
        sub_category_id,
        product_id: productToDelete,
      });

      if (response.data.status_code === 200) {
        setProducts(products.filter((product) => product.product_id !== productToDelete));
        setMessage(`${productNameToDelete} deleted successfully!`);
        setShowDeletePopup(false);
        setShowActionSuccessPopup(true);
      } else {
        alert(response.data.error || "Failed to delete product.");
      }
    } catch (error) {
      alert("Error deleting product. Please try again.");
    }
  };

  const handleProductClick = (product) => {
    if (!product || !product.product_id || !product.product_name) {
      console.error("Invalid product data");
      return;
    }
    
    const adminId = sessionStorage.getItem("admin_id");
  
    navigate("/view-product-details", {
      state: {
        admin_id: adminId,
        category_id,
        category_name,
        sub_category_id,
        sub_category_name,
        product_id: product.product_id,
      },
    });
  };
  
  return (
    <div>
      <div className="category-div">
        <div className="category-heading">Products</div>
        {error && <p className="error-message">{error}</p>}
        {!loading && products.length === 0 && <p className="no-data">No products found.</p>}
      </div>

      <div className="category-cards product-cards">
        {products.map((product) => (
          <div key={product.product_id} className="category-card product-card">
            <img
              src={product.product_images}
              alt={product.product_name}
              className="card-image"
              onClick={() => handleProductClick(product)}
            />
            <div className="product-info">
              <p className="card-name">{product.product_name || "N/A"}</p>
              <p className="card-code">SKU: {product.sku_number || "N/A"}</p>
              <p className="card-price">
                <FaRupeeSign /> {product.price || "N/A"}/- (Incl GST)
              </p>
            </div>
            <div className="card-menu">
              <div onClick={() => handleEditProduct(product)} className="edit-label">
                <FaEdit className="edit-icon" />
                <span className="card-menu-icon-label edit-label">Edit</span>
              </div>
              <div
                onClick={() => {
                  setProductToDelete(product.product_id);
                  setProductNameToDelete(product.product_name);
                  setShowDeletePopup(true);
                }}
                className="delete-label"
              >
                <FaTrash className="delete-icon" />
                <span className="card-menu-icon-label delete-label">Delete</span>
              </div>
            </div>
          </div>
        ))}

        <div className="add-category-card" onClick={handleAddProduct}>
          <img src={AddIcon} alt="Add Product" className="add-category-image" />
        </div>
      </div>

      {/* Delete Confirmation Popup */}
      {showDeletePopup && (
        <div className="popup-overlay">
          <div className="popup-content">
            <p>
              Are you sure you want to delete <strong>"{productNameToDelete}"</strong> product?
            </p>
            <div className="popup-buttons">
              <button className="popup-confirm" onClick={handleDeleteProduct}>
                Yes, Delete
              </button>
              <button className="popup-cancel" onClick={() => setShowDeletePopup(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Popup */}
      {showActionSuccessPopup && (
        <div className="popup-overlay">
          <div className="popup-content">
            <FaTimes className="popup-close-icon" onClick={() => setShowActionSuccessPopup(false)} />
            <div className="message">
              <FaCircleCheck className="success-icon" />
              <p className="success-message-text">
                <strong>{message}</strong>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ViewProducts;
