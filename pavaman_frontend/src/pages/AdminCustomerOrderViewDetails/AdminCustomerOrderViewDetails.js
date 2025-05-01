import React, { useEffect, useState } from 'react';
import { useParams } from "react-router-dom";
import axios from 'axios';
import "./AdminCustomerOrderViewDetails.css";
import PopupMessage from "../../components/Popup/Popup";

const PaidOrderDetails = () => {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [productStatuses, setProductStatuses] = useState({});
  const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
  const [showPopup, setShowPopup] = useState(false);

  const displayPopup = (text, type = "success") => {
    setPopupMessage({ text, type });
    setShowPopup(true);
    setTimeout(() => setShowPopup(false), 5000);
  };

  useEffect(() => {
    const fetchOrderDetails = async () => {
      try {
        const adminId = sessionStorage.getItem("admin_id");
        const response = await axios.post(
          "http://127.0.0.1:8000/get-payment-details-by-order",
          {
            razorpay_order_id: orderId,
            admin_id: adminId
          },
          { withCredentials: true }
        );

        const matchedOrder = response.data.payments.find(
          (payment) => payment.razorpay_order_id === orderId
        );

        if (matchedOrder) {
          setOrder(matchedOrder);
          const statuses = {};
          matchedOrder.order_products.forEach((product) => {
            statuses[product.id] = {
              shipped: product.shipping_status?.toLowerCase().trim() === "shipped",
              delivered: product.delivery_status?.toLowerCase().trim() === "delivered"
            };
          });
          
          setProductStatuses(statuses);
        }
      } catch (error) {
        console.error("Error fetching order details:", error);
      }
    };

    fetchOrderDetails();
  }, [orderId]);

  
  const updateProductStatus = async (productId, statusType) => {
    const admin_id = sessionStorage.getItem("admin_id");
    const customer_id = order.customer_id;
    const product_order_id = order.product_order_id;
  
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/order-or-delivery-status",
        {
          admin_id,
          customer_id,
          product_order_id,
          action: statusType === "shipped" ? "Shipped" : "Delivered",
          single_order_product_id: productId
        },
        { withCredentials: true }
      );
  
      if (response.data.status_code === 200) {
        setProductStatuses((prevStatuses) => ({
          ...prevStatuses,
          [productId]: {
            ...prevStatuses[productId],
            [statusType === "shipped" ? "shipped" : "delivered"]: true
          }
        }));
        displayPopup(`${statusType === "shipped" ? "Shipped" : "Delivered"} status updated.`);
      } else {
        displayPopup("Failed to update status.", "error");
      }
    } catch (error) {
      console.error("Error updating status:", error);
      displayPopup("An error occurred while updating status.", "error");
    }
  };
  
  const updateAllStatus = async (statusType) => {
    const admin_id = sessionStorage.getItem("admin_id") || 1;
    const customer_id = order.customer_id;
    const product_order_id = order.product_order_id;
  
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/order-or-delivery-status",
        {
          admin_id,
          customer_id,
          product_order_id,
          action: statusType === "shipped" ? "Shipped" : "Delivered"
        },
        { withCredentials: true }
      );
  
      if (response.data.status_code === 200) {
        const updatedIds = response.data.updated_orders || [];
  
        const updatedStatuses = { ...productStatuses };
        updatedIds.forEach((id) => {
          if (!updatedStatuses[id]) updatedStatuses[id] = {};
          updatedStatuses[id][statusType === "shipped" ? "shipped" : "delivered"] = true;
        });
  
        setProductStatuses(updatedStatuses);
        displayPopup(`All products marked as ${statusType === "shipped" ? "Shipped" : "Delivered"}.`);
      } else {
        displayPopup("Failed to update all statuses.", "error");
      }
    } catch (error) {
      console.error("Error updating all statuses:", error);
      displayPopup("An error occurred while updating all statuses.", "error");
    }
  };
  

  const allshipped = Object.values(productStatuses).every(s => s.shipped);
  const allDelivered = Object.values(productStatuses).every(s => s.delivered);

  if (!order) return <div className="loading">Loading...</div>;

  const {
    customer_name,
    email,
    mobile_number,
    customer_address,
    order_products
  } = order;

  const address = customer_address[0] || {};

  return (
    <div className="report-details-container">
      {showPopup && <PopupMessage text={popupMessage.text} type={popupMessage.type} />}
      <div className="customer-address-box">
        <div className="details-row">
          <div className="details-column">
            <h2>Customer Details</h2>
            <div className='detail-item'><strong>Name:</strong> {customer_name}</div>
            <div className='detail-item'><strong>Email:</strong> {email}</div>
            <div className='detail-item'><strong>Mobile:</strong> {mobile_number}</div>
          </div>
          <div className="details-column">
            <h2>Delivery Address</h2>
            <div className='address-details-columns'>
              <div className='first-address-details-column'>
                <div className='detail-item'><strong>Name:</strong> {address.customer_name}</div>
                <div className='detail-item'><strong>Mobile:</strong> {address.mobile_number}</div>
                <div className='detail-item'><strong>Alternate:</strong> {address.alternate_mobile}</div>
                <div className='detail-item'><strong>Type:</strong> {address.address_type}</div>
                <div className='detail-item'><strong>Street:</strong> {address.street}</div>
              </div>
              <div className='second-address-details-column'>
                <div className='detail-item'><strong>Village:</strong> {address.village}</div>
                <div className='detail-item'><strong>District:</strong> {address.district}</div>
                <div className='detail-item'><strong>State:</strong> {address.state}</div>
                <div className='detail-item'><strong>Pincode:</strong> {address.pincode}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="product-details-table">
        <h3>Payment Order Details</h3>
        {order_products?.length ? (
          <table>
            <thead>
              <tr>
                <th>Image</th>
                <th>Product Name</th>
                <th>Unit Price</th>
                <th>Discount</th>
                <th>Final Price</th>
                <th>Quantity</th>
                <th>Total</th>
                <th>Shipping Status</th>
                <th>Delivery Status</th>
                <th>Shipping</th>
                <th>Deliver</th>
              </tr>
            </thead>
            <tbody>
              {order_products.map((item) => (
                <tr key={item.id}>
                  <td>
                    {item.product_image ? (
                      <img
                        src={`http://127.0.0.1:8000/${item.product_image}`}
                        alt={item.product_name}
                        height="50"
                      />
                    ) : "No image"}
                  </td>
                  <td>{item.product_name}</td>
                  <td>₹{item.price}</td>
                  <td>₹{item.discount}</td>
                  <td>₹{item.final_price}</td>
                  <td>{item.quantity}</td>
                  <td>₹{item.final_price * item.quantity}</td>
                  <td>{productStatuses[item.id]?.shipped ? "Shipped" : "Pending"}</td>
<td>{productStatuses[item.id]?.delivered ? "Delivered" : "Pending"}</td>

                 <td>
  <input
    type="checkbox"
    checked={productStatuses[item.id]?.shipped || false}
    onChange={() => updateProductStatus(item.id, "shipped")}
    disabled={
      productStatuses[item.id]?.shipped || 
      productStatuses[item.id]?.delivered
    }
  />
</td>
<td>
  <input
    type="checkbox"
    checked={productStatuses[item.id]?.delivered || false}
    onChange={() => updateProductStatus(item.id, "delivered")}
    disabled={
      productStatuses[item.id]?.delivered || 
      !productStatuses[item.id]?.shipped
    }
  />
</td>



                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan="9"></td>
                <td>
                  <label>
                  <input
  type="checkbox"
  checked={allshipped}
  onChange={() => updateAllStatus("shipped")}
  disabled={allshipped || allDelivered}
/>

                    Select All
                  </label>
                </td>
                <td>
                  <label>
                  <input
  type="checkbox"
  checked={allDelivered}
  onChange={() => updateAllStatus("delivered")}
  disabled={allDelivered}
/>

                    Select All
                  </label>
                </td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <p>No products found for this order.</p>
        )}
      </div>
    </div>
  );
};

export default PaidOrderDetails;
