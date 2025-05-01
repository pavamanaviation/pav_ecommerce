import React, { useEffect, useRef, useState } from 'react';
import './CustomerMyOrderDetails.css';
import { useLocation } from 'react-router-dom';
import { FaCircleArrowRight } from "react-icons/fa6";
import { MdCloudDownload } from "react-icons/md";
import generateInvoicePDF from '../CustomerInvoice/CustomerInvoice'; // Import the function

const CustomerMyOrderDetails = () => {
  const [orderDetails, setOrderDetails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const location = useLocation();
  const { payments, order, selected_product_id } = location.state || {};
  const customerId = localStorage.getItem("customer_id");
  const topRef = useRef(null);

  useEffect(() => {
    const fetchOrderData = async () => {
      if (!customerId) return;

      try {
        const response = await fetch('http://127.0.0.1:8000/customer-my-order', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ customer_id: customerId }),
        });

        const data = await response.json();
        if (data.status_code === 200) {
          setOrderDetails(data.payments || []);
        }
      } catch (error) {
        console.error('Fetch error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOrderData();
  }, [customerId]);

  useEffect(() => {
    if (selected_product_id && order?.order_products?.length) {
      const initialProduct = order.order_products.find(
        (prod) => prod.order_product_id === selected_product_id
      );
      setSelectedProduct(initialProduct || order.order_products[0]);
    } else if (order?.order_products?.length) {
      setSelectedProduct(order.order_products[0]);
    }
  }, [order]);

  const handleProductClick = (product) => {
    setSelectedProduct(product);
    if (topRef.current) {
      topRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleGetInvoice = () => {
    if (selectedProduct) {
      generateInvoicePDF(customerId, order);
    }
  };

  if (loading) return <div className="order-loader">Loading...</div>;
  if (!orderDetails.length) return <div className="order-loader"><p>No orders found.</p></div>;

  const orderHasMultipleProducts = order?.order_products?.length > 1;
  const otherProducts = order?.order_products?.filter(
    (prod) => prod.order_product_id !== selectedProduct?.order_product_id
  );

  return (
    <div className="order-box">
      <h4 className="main-heading">Order ID: {order.product_order_id}</h4>

      {/* Selected Product Block */}
      {selectedProduct && (
        <div ref={topRef}>
          <div className="custom-product-card highlight-product">
            <img
              src={selectedProduct.product_image}
              alt={selectedProduct.product_name}
              className="custom-product-image"
            />
            <div className="custom-product-info">
              <h5 className="custom-product-title">{selectedProduct.product_name}</h5>
              <p><strong>Quantity:</strong> {selectedProduct.quantity}</p>
              <p><strong>Price:</strong> ₹{selectedProduct.final_price}</p>
            </div>
          </div>

          {/* Address */}
          {order.customer_address?.length > 0 && (
            <div className="shipping-address-box">
              <h3>Delivery Address</h3>
              <p><strong>{order.customer_name}</strong></p>
              <p>{order.customer_address[0].street}, {order.customer_address[0].landmark}, {order.customer_address[0].village},{order.customer_address[0].mandal}</p>
              <p>{order.customer_address[0].postoffice}, {order.customer_address[0].district},{order.customer_address[0].state} - {order.customer_address[0].pincode},{order.customer_address[0].country}</p>
              <p><strong>Phone:</strong> {order.customer_address[0].mobile_number}</p>
            </div>
          )}

          {/* Per Product Payment Details */}
          <div className="payment-box">
            <h3 className='payment-details-heading'>
              {orderHasMultipleProducts
                ? `Payment Details for ${selectedProduct.product_name}`
                : 'Total Payment'}
            </h3>
            <p><strong>Payment Mode:</strong> {order.payment_mode}</p>
            <p><strong>Quantity:</strong> {selectedProduct.quantity}</p>
            <p><strong>Price:</strong> ₹{selectedProduct.final_price}</p>

            {/* Invoice button only for single-product orders */}
            {!orderHasMultipleProducts && (
              <div className="invoice-button-wrapper">
                <button className="invoice-button" onClick={handleGetInvoice}>
                  Get Invoice <MdCloudDownload className="invoice-icon" />
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Other Products */}
      {otherProducts?.length > 0 && (
        <>
          <h4 className="other-items-heading">Other items in this order</h4>
          {otherProducts.map((product, index) => (
            <div key={index} className="custom-product-card">
              <img
                src={product.product_image}
                alt={product.product_name}
                className="custom-product-image"
              />
              <div className="custom-product-info">
                <h5 className="custom-product-title">{product.product_name}</h5>
                <p><strong>Quantity:</strong> {product.quantity}</p>
                <p><strong>Price:</strong> ₹{product.final_price}</p>
              </div>
              <div className="custom-arrow-button" onClick={() => handleProductClick(product)}>
                <FaCircleArrowRight />
              </div>
            </div>
          ))}
        </>
      )}

      {/* Total Payment Section for Multiple Products */}
      {orderHasMultipleProducts && (
        <div className="payment-box total-payment">
          <h3>Total Payment</h3>
          <p><strong>Total Quantity:</strong> {order.total_quantity}</p>
          <p><strong>Total Price:</strong> ₹{order.total_amount}</p>
          <p><strong>Payment Date:</strong> {order.payment_date}</p>
          <div className="invoice-button-wrapper">
            <button className="invoice-button" onClick={handleGetInvoice}>
              Get Invoice <MdCloudDownload className="invoice-icon" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerMyOrderDetails;