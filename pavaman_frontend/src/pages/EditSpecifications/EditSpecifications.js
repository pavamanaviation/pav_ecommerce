import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";

const EditSpecification = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { admin_id, category_id, sub_category_id, product_id, specifications } = location.state || {};

  // Convert object to array format for editing
  const initialSpecs = specifications
    ? Object.entries(specifications).map(([name, value]) => ({ name, value }))
    : [];

  const [specs, setSpecs] = useState(initialSpecs);

  const handleChange = (index, field, value) => {
    const updatedSpecs = [...specs];
    updatedSpecs[index][field] = value;
    setSpecs(updatedSpecs);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const requestData = {
      admin_id,
      category_id,
      sub_category_id,
      product_id,
      number_of_specifications: specs.length,
      specifications: specs,
    };

    try {
      const response = await axios.post("http://127.0.0.1:8000/edit-product-specifications", requestData);
      if (response.data.status_code === 200) {
        alert("Specifications updated successfully!");
        navigate(-1); // Go back to product details page
      } else {
        alert("Failed to update specifications.");
      }
    } catch (error) {
      alert("Error updating specifications. Please try again.");
    }
  };

  return (
    <div>
      <h2>Edit Specifications</h2>
      <form onSubmit={handleSubmit}>
        {specs.map((spec, index) => (
          <div key={index}>
            <label>Specification Name:</label>
            <input
              type="text"
              value={spec.name}
              onChange={(e) => handleChange(index, "name", e.target.value)}
              readOnly // Prevent name editing
            />
            <label>Value:</label>
            <input
              type="text"
              value={spec.value}
              onChange={(e) => handleChange(index, "value", e.target.value)}
            />
          </div>
        ))}
        <button type="submit">Update Specifications</button>
      </form>
      <button onClick={() => navigate(-1)}>Cancel</button>
    </div>
  );
};

export default EditSpecification;
