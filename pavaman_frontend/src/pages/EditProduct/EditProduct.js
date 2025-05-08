import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import "../EditProduct/EditProduct.css";
import UploadFileIcon from "../../assets/images/upload-file-icon.svg";
import SuccessIcon from "../../assets/images/succes-icon.png";

const EditProduct = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const productData = location.state || {};
  const { category_id, category_name, sub_category_id, sub_category_name } = location.state || {};

  const [product, setProduct] = useState({
    product_name: productData.product_name || "",
    sku_number: productData.sku_number || "",
    price: productData.price || "",
    quantity: productData.quantity || "",
    discount: productData.discount !== undefined ? productData.discount : "",
    description: productData.description || "",
    product_images: productData.product_images || [], 
    material_file: null,
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!productData.product_id) {
      setError("Invalid product data. Please go back and try again.");
    }
  }, [productData]);

  const handleChange = (e) => {
    setProduct({ ...product, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    const { name, files } = e.target;

    if (files.length === 0) return;

    setProduct((prev) => {
      if (name === "product_images") {
        return { ...prev, product_images: Array.from(files) };
      } else if (name === "material_file") {
        return { ...prev, material_file: files[0] };
      }
      return prev;
    });

    console.log(`${name} updated. Selected ${files.length} file(s).`);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const adminId = sessionStorage.getItem("admin_id");

    if (!adminId) {
      alert("Session expired. Please log in again.");
      navigate("/admin-login");
      return;
    }

    const formDataToSend = new FormData();
    formDataToSend.append("admin_id", adminId);
    formDataToSend.append("category_id", category_id);
    formDataToSend.append("sub_category_id", sub_category_id);
    formDataToSend.append("product_id", productData.product_id);

    Object.keys(product).forEach((key) => {
      if (key === "product_images") {
        if (product.product_images.length > 0 && product.product_images[0] instanceof File) {
          product.product_images.forEach((file) => {
            formDataToSend.append("product_images", file);
          });
        } else {
          formDataToSend.append("existing_images", JSON.stringify(product.product_images));
        }
      } else {
        formDataToSend.append(key, product[key]);
      }
    });

    try {
      const response = await axios.post("http://65.0.183.78:8000/edit-product", formDataToSend);
      if (response.data.status_code === 200) {
        // alert("Product updated successfully.");
        navigate("/view-products", {
          state: { category_id, category_name, sub_category_id, sub_category_name, successMessage: "Product updated successfully!" },
        });
      } else {
        setError(response.data.error || "Failed to update product.");
      }
    } catch (err) {
      setError("Error updating product. Please try again.");
      console.error("API Error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="edit-product-container">
      <h2  className="form-title">Edit Product</h2>

      {error && <p className="error-message">{error}</p>}

      <form onSubmit={handleSubmit} className="add-product-form">
        <div>
          <label className="label">Name of the Category</label>
          <input type="text" name="category_name" value={category_name || ""} disabled className="input-field disabled" />
        </div>
        <div>
          <label className="label">Name of the SubCategory</label>
          <input type="text" name="sub_category_name" value={sub_category_name || ""} disabled className="input-field disabled" />
        </div>
        <div>
          <label className="label">Product Name</label>
          <input type="text" name="product_name" value={product.product_name} onChange={handleChange} required className="input-field" />
        </div>
        <div className="input-row">
          <div>
            <label className="label">SKU</label>
            <input type="text" name="sku_number" value={product.sku_number} onChange={handleChange} required className="input-field" />
          </div>
          <div>
            <label className="label">Price</label>
            <input type="number" name="price" value={product.price} onChange={handleChange} required className="input-field" />
          </div>
        </div>
        <div className="input-row">
          <div>
            <label className="label">Quantity</label>
            <input type="number" name="quantity" value={product.quantity} onChange={handleChange} required className="input-field" />
          </div>
          <div>
            <label className="label">Discount</label>
            <input type="number" name="discount" value={product.discount} onChange={handleChange} className="input-field" />
          </div>
        </div>
        <div>
          <label className="label">Description</label>
          <textarea name="description" value={product.description} onChange={handleChange} required className="textarea-field"></textarea>
        </div>

        {/* Upload Product Images */}
        <div className="upload-file">
          <label htmlFor="product_images" className="upload-label">Upload (1 or more) Product Images</label>
          <div className="upload-box">
            {product.product_images.length > 0 ? (
              <div className="success-icon">
                <img src={SuccessIcon} alt="Success Icon" className="success-icon-img" />
                <p>Successfully uploaded file(s) uploaded</p>
              </div>
            ) : (
              <>
                <img src={UploadFileIcon} alt="Upload Icon" className="upload-icon" />
                <p className="upload-text"><span>Upload File(s)</span> or Drag and Drop</p>
              </>
            )}
            <input type="file" id="product_images" name="product_images" multiple className="upload-input" onChange={handleFileChange} />
          </div>
        </div>

        {/* Upload Material File */}
        <div className="upload-file">
          <label htmlFor="material_file" className="upload-label">Upload Material File</label>
          <div className="upload-box">
            {product.material_file ? (
              <div className="success-icon">
                <img src={SuccessIcon} alt="Success Icon" className="success-icon-img" />
                <p>Successfully uploaded file</p>
              </div>
            ) : (
              <>
                <img src={UploadFileIcon} alt="Upload Icon" className="upload-icon" />
                <p className="upload-text"><span>Upload File</span> or Drag and Drop</p>
                {/* <p className="upload-text-mb">Up to 20MB</p> */}
              </>
            )}
            <input type="file" id="material_file" name="material_file" className="upload-input" onChange={handleFileChange} />
          </div>
        </div>

        <div className="button-group">
          <button type="button" className="admin-cancel-button" onClick={() => navigate(-1)}>Cancel</button>
          <button type="submit" className="admin-submit-button" disabled={loading}>Update</button>
        </div>
      </form>
    </div>
  );
};

export default EditProduct;
