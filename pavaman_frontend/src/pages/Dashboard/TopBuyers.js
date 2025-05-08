import React, { useEffect, useState } from "react";
import axios from "axios";
// import "./TopBuyersPage.css"; // Create or reuse shared CSS

const TopBuyersPage = () => {
  const [buyers, setBuyers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const admin_id = sessionStorage.getItem("admin_id");

  useEffect(() => {
    axios
      .post("http://65.0.183.78:8000/top-buyers-report", { admin_id })
      .then((res) => {
        setBuyers(res.data.buyers || []);
        setLoading(false);
      })
      .catch((err) => {
        setError("Failed to load top buyers.");
        setLoading(false);
      });
  }, []);

  return (
    <div className="report-wrapper">
      <h2 className="report-title">All Top Buyers</h2>

      {loading && <p className="loading-text">Loading top buyers...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <div className="report-table-container">
          <table className="report-table">
            <thead>
              <tr>
                <th>S.No.</th>
                <th>Name</th>
                <th>Email</th>
                <th>Mobile</th>
                <th>Products Bought</th>
                <th>Total Quantity</th>
              </tr>
            </thead>
            <tbody>
              {buyers.map((buyer, index) => (
                <tr key={buyer.customer_id}>
                  <td className="order-table-data">{index + 1}</td>
                  <td className="order-table-data">{buyer.name}</td>
                  <td className="order-table-data text-style">{buyer.email}</td>
                  <td className="order-table-data">{buyer.mobile_no}</td>
                  <td className="order-table-data">{buyer.product_count}</td>
                  <td className="order-table-data">{buyer.total_quantity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TopBuyersPage;
