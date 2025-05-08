import React, { useEffect, useState } from "react";
import axios from "axios";
// import "./LowStockProductsPage.css"; // make sure to create this or use existing styles

const LowStockProductsPage = () => {
  const [lowStock, setLowStock] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const admin_id = sessionStorage.getItem("admin_id");

  useEffect(() => {
    axios
      .post("http://65.0.183.78:8000/report-inventory-summary", { admin_id })
      .then((res) => {
        setLowStock(res.data.low_stock_products || []);
        setLoading(false);
      })
      .catch((err) => {
        setError("Failed to load low stock products.");
        setLoading(false);
      });
  }, []);

  return (
    <div className="report-wrapper">
      <h2 className="report-title">All Low Stock Products</h2>

      {loading && <p className="loading-text">Loading products...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <div className="report-table-container">
          <table className="report-table">
            <thead>
              <tr>
                <th>S.No.</th>
                <th>Product Name</th>
                <th>Quantity</th>
              </tr>
            </thead>
            <tbody>
              {lowStock.map((product, index) => (
                <tr key={product.product_id}>
                  <td className="order-table-data">{index + 1}</td>
                  <td className="order-table-data">{product.product_name}</td>
                  <td className="order-table-data">{product.quantity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default LowStockProductsPage;
