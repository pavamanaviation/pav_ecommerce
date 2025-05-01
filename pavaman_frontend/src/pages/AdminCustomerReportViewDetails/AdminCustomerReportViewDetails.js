// import React, { useEffect, useState } from 'react';
// import { useParams } from "react-router-dom";
// import axios from 'axios';
// import './AdminCustomerReportViewDetails.css'; // Make sure this CSS file exists

// const PaidOrderDetails = () => {
//   const { orderId } = useParams();
//   const [order, setOrder] = useState(null);

//   useEffect(() => {
//     const fetchOrderDetails = async () => {
//       try {
//         const adminId = sessionStorage.getItem("admin_id") || 1;
//         const response = await axios.post(
//           "http://127.0.0.1:8000/get-payment-details-by-order",
//           {
//             razorpay_order_id: orderId,
//             admin_id: adminId
//           },
//           { withCredentials: true }
//         );

//         const matchedOrder = response.data.payments.find(
//           (payment) => payment.razorpay_order_id === orderId
//         );

//         if (matchedOrder) {
//           setOrder(matchedOrder);
//         } else {
//           console.error("Order not found");
//         }
//       } catch (error) {
//         console.error("Error fetching order details:", error);
//       }
//     };

//     fetchOrderDetails();
//   }, [orderId]);

//   if (!order) return <div className="loading">Loading...</div>;

//   const {
//     customer_name,
//     email,
//     mobile_number,
//     customer_address,
//     order_products
//   } = order;

//   const address = customer_address[0] || {};

//   return (
//     <div className="report-details-container">

//       {/* Customer Info & Delivery Address */}
//       <div className="customer-address-box">
//         <div className="details-row">
          
//           <div className="details-column">
//             <h2>Customer Details</h2>
//             <div className='detail-item'><strong>Name:</strong> {customer_name}</div>
//             <div className='detail-item'><strong>Email:</strong> {email}</div>
//             <div className='detail-item'><strong>Mobile:</strong> {mobile_number}</div>
//           </div>

//           <div className="details-column">
//             <h2> Delivery Address</h2>
//             <div className='address-details-columns'>

//             <div className='first-address-details-column'>

//             <div className='detail-item'><strong>Name:</strong> {address.customer_name}</div>
//             <div className='detail-item'><strong>Mobile:</strong> {address.mobile_number}</div>
//             <div className='detail-item'><strong>Alternate Mobile:</strong> {address.alternate_mobile}</div>
//             <div className='detail-item'><strong>Type:</strong> {address.address_type}</div>
//             <div className='detail-item'><strong>Street:</strong> {address.street}</div>
//             </div>
//             <div className='second-address-details-column'>

//             <div className='detail-item'><strong>Village:</strong> {address.village}</div>
//             <div className='detail-item'><strong>District:</strong> {address.district}</div>
//             <div className='detail-item'><strong>State:</strong> {address.state}</div>
//             <div className='detail-item'><strong>Pincode:</strong> {address.pincode}</div>
//             </div>
//             </div>
//           </div>

//         </div>
//       </div>

//       {/* Product Table */}
//       <div className="product-details-table">
//         <h3>Payment Order Details</h3>
//         {order_products && order_products.length > 0 ? (
//           <table>
//             <thead>
//               <tr>
//                 <th>Image</th>
//                 <th>Product Name</th>
//                 <th>Unit Price</th>
//                 <th>Discount</th>
//                 <th>Final Price</th>
//                 <th>Quantity</th>
//                 <th>Total Price</th>
//               </tr>
//             </thead>
//             <tbody>
//               {order_products.map((item, index) => (
//                 <tr key={index}>
//                   <td>
//                     {item.product_image ? (
//                       <img
//                         src={`http://127.0.0.1:8000/${item.product_image}`}
//                         alt={item.product_name}
//                         height="50"
//                       />
//                     ) : (
//                       "No image"
//                     )}
//                   </td>
//                   <td>{item.product_name}</td>
//                   <td>₹{item.price}</td>
//                   <td>₹{item.discount}</td>
//                   <td>₹{item.final_price}</td>
//                   <td>{item.quantity}</td>
//                   <td>₹{item.final_price * item.quantity}</td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         ) : (
//           <p>No products found for this order.</p>
//         )}
//       </div>

//     </div>
//   );
// };

// export default PaidOrderDetails;