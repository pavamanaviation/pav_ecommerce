import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import "./AdminRatings.css";

const AdminRatings = () => {
  const [feedbackList, setFeedbackList] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 10;

  const adminId = sessionStorage.getItem("admin_id");

  useEffect(() => {
    const fetchFeedback = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await fetch('http://127.0.0.1:8000/retrieve-feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ admin_id: adminId }),
        });

        const data = await response.json();

        if (response.ok) {
          const startIndex = (currentPage - 1) * itemsPerPage;
          const paginatedData = data.feedback.slice(startIndex, startIndex + itemsPerPage);
          setFeedbackList(paginatedData);
          setTotalPages(Math.ceil(data.feedback.length / itemsPerPage));
        } else {
          setError(data.error || 'An error occurred');
        }
      } catch (err) {
        setError('Server error: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchFeedback();
  }, [adminId, currentPage]);

  const prevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const nextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const paginate = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  return (
    <div className="report-wrapper">
      <h2 className="report-title">Feedback Reports</h2>
      {loading && <p className="loading-text">Loading feedback...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && (
        <>
          <div className="report-table-container">
            <table className="report-table">
              <thead>
                <tr>
                  <th>S.No.</th>
                  <th>Product Image</th>
                  <th>Product Name</th>
                  <th>Order ID</th>
                  <th>Rating</th>
                  <th>Feedback</th>
                  <th>Created At</th>
                  <th>Customer Name</th>
                  <th>Customer Email</th>
                </tr>
              </thead>
              <tbody>
                {feedbackList.map((item, index) => (
                  <tr key={index}>
                    <td className="order-table-data">{(currentPage - 1) * itemsPerPage + index + 1}</td>
                    <td className="order-table-data"><img src={item.product_image} /></td>
                    <td className="order-table-data">{item.product_name}</td>
                    <td className="order-table-data">{item.order_id}</td>
                    <td className="order-table-data">{item.rating}</td>
                    <td className="order-table-data">{item.feedback}</td>
                    <td className="order-table-data">{item.created_at}</td>
                    <td className="order-table-data">{item.customer_name}</td>
                    <td className="order-table-data text-style">{item.customer_email}</td>

                   
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination-container">
            <button
              onClick={prevPage}
              disabled={currentPage === 1}
              className="pagination-button"
            >
              Previous
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                onClick={() => paginate(page)}
                className={`pagination-button ${page === currentPage ? 'active-page' : ''}`}
              >
                {page}
              </button>
            ))}

            <button
              onClick={nextPage}
              disabled={currentPage === totalPages}
              className="pagination-button"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminRatings;
