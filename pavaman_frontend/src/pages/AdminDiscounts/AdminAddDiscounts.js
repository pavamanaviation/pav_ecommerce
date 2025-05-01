import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import "./AdminAddDiscount.css";

const AdminAddDiscount = () => {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [selectedSubcategories, setSelectedSubcategories] = useState([]);
  const [categoryId, setCategoryId] = useState('');
  const [discount, setDiscount] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    const adminId = sessionStorage.getItem("admin_id");
    if (!adminId) return navigate("/admin-login");

    try {
      const response = await fetch("http://127.0.0.1:8000/view-categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin_id: adminId }),
      });

      const data = await response.json();
      if (response.ok) setCategories(data.categories || []);
      else setError(data.error || "Failed to fetch categories.");
    } catch {
      setError("Server error while fetching categories.");
    }
  };

  const fetchSubcategories = async (selectedCategoryId) => {
    const adminId = sessionStorage.getItem("admin_id");
    if (!adminId || !selectedCategoryId) return;

    try {
      const response = await fetch("http://127.0.0.1:8000/view-subcategories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          admin_id: adminId,
          category_id: selectedCategoryId
        })
      });

      const data = await response.json();
      if (response.ok) {
        setSubcategories(data.subcategories || []);
        setSelectedSubcategories([]);
      } else {
        setSubcategories([]);
        setSelectedSubcategories([]);
      }
    } catch {
      setSubcategories([]);
      setSelectedSubcategories([]);
    }
  };

  const handleCategoryChange = (e) => {
    const selectedId = e.target.value;
    setCategoryId(selectedId);
    setSubcategories([]);
    fetchSubcategories(selectedId);
  };

  const handleSubcategoryCheckbox = (id) => {
    setSelectedSubcategories(prev =>
      prev.includes(id) ? prev.filter(subId => subId !== id) : [...prev, id]
    );
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');
    const adminId = sessionStorage.getItem('admin_id');

    if (!categoryId || selectedSubcategories.length === 0 || !discount) {
      setError('Please select category, at least one subcategory, and enter a discount.');
      return;
    }

    if (!discount.endsWith('%')) {
      setError('Discount must end with "%", e.g., 10%.');
      return;
    }

    const selectedCategory = categories.find(cat => cat.category_id === categoryId);
    const payload = {
      admin_id: adminId,
      categories: selectedSubcategories.map(subId => {
        const sub = subcategories.find(sub => String(sub.id) === subId);
        return {
          category_id: categoryId,
          category_name: selectedCategory?.category_name,
          sub_category_id: subId,
          sub_category_name: sub?.sub_category_name,
          discount: discount
        };
      })
    };

    try {
      const response = await axios.post('http://127.0.0.1:8000/apply-discount-subcategory', payload);
      if (response.data.status_code === 200) {
        setSuccess('Discount applied successfully!');
        setTimeout(() => navigate('/discounts'), 2000);
      } else {
        setError(response.data.error || 'Failed to apply discount.');
      }
    } catch {
      setError('Server error while applying discount.');
    }
  };

  const handleSelectAll = (e) => {
    const isChecked = e.target.checked;
    if (isChecked) {
      const allIds = subcategories.map(sub => String(sub.id));
      setSelectedSubcategories(allIds);
    } else {
      setSelectedSubcategories([]);
    }
  };
  
  const isAllSelected = subcategories.length > 0 && selectedSubcategories.length === subcategories.length;
  

  return (
    <div className="add-discount-container">
      <div className='add-discount-heading'>Add Discount</div>

      <div className="discount-form-group">
        <label className="discount-form-group-label">Category</label>
        <select
          className="discount-form-group-input"
          value={categoryId}
          onChange={handleCategoryChange}
        >
          <option value="">Select Category</option>
          {categories.map(cat => (
            <option key={cat.category_id} value={cat.category_id}>
              {cat.category_name}
            </option>
          ))}
        </select>
      </div>

      {subcategories.length === 0 && categoryId && (
        <p className="no-subcategory-message">No subcategories available for the selected category.</p>
      )}

      {subcategories.length > 0 && (
        <div className="subcategory-table-container">
          <table className="subcategory-table">
          <thead>
  <tr>
    <th className="discount-table-group-label">S.No</th>
    <th className="discount-table-group-label">Subcategory Name</th>
    <th className="discount-table-group-label">
      <input
        type="checkbox"
        checked={isAllSelected}
        onChange={handleSelectAll}
      /> Select All / Select
    </th>
  </tr>
</thead>

            <tbody>
  {subcategories.map((sub, index) => (
    <tr key={sub.id}>
      <td>{index + 1}</td>
      <td>{sub.sub_category_name}</td>
      <td>
        <input
          type="checkbox"
          checked={selectedSubcategories.includes(String(sub.id))}
          onChange={() => handleSubcategoryCheckbox(String(sub.id))}
        />
      </td>
    </tr>
  ))}
</tbody>

          </table>
        </div>
      )}

{categoryId && selectedSubcategories.length > 0 && (
  <div className="discount-form-group">
    <label className="discount-form-group-label">Discount</label>
    <input
      type="text"
      value={discount}
      onChange={(e) => setDiscount(e.target.value)}
      placeholder="Enter Discount (example: 10%)"
      className="discount-form-group-input"
    />
  </div>
)}


      {error && <p className="error-message">{error}</p>}
      {success && <p className="success-message">{success}</p>}

      <div className="discount-button-group">
        <button className="cart-place-order" onClick={handleSave}>Save</button>
        <button className="cart-delete-selected" onClick={() => navigate("/discounts")}>Cancel</button>
      </div>
    </div>
  );
};

export default AdminAddDiscount;
