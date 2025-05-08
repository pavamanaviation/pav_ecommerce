import React, { useEffect, useState } from "react";
import axios from "axios";
import "../Dashboard/Dashboard.css";
import { PiHandCoinsBold } from "react-icons/pi";
import { GiCoins } from "react-icons/gi";
import { BsCoin } from "react-icons/bs";
import { SlPeople } from "react-icons/sl";
import { FaBoxOpen } from "react-icons/fa6";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
    const [summaryData, setSummaryData] = useState(null);
    const [topBuyers, setTopBuyers] = useState([]);
    const [currentMonthOrders, setCurrentMonthOrders] = useState(null);
    const [lowStockProducts, setLowStockProducts] = useState([]);
    const navigate = useNavigate();
    const admin_id = sessionStorage.getItem("admin_id");

    useEffect(() => {
        fetchSummary();
        fetchTopBuyers();
        fetchMonthlyOrders();
    }, []);

    const fetchSummary = async () => {
        try {
            const response = await axios.post("http://65.0.183.78:8000/report-inventory-summary", { admin_id });
            setSummaryData(response.data);
            setLowStockProducts(response.data.low_stock_products || []);
        } catch (error) {
            console.error("Error fetching summary:", error);
        }
    };

    const fetchTopBuyers = async () => {
        try {
            const response = await axios.post("http://65.0.183.78:8000/top-buyers-report", { admin_id });
            setTopBuyers(response.data.buyers || []);
        } catch (error) {
            console.error("Error fetching top buyers:", error);
        }
    };

    const fetchMonthlyOrders = async () => {
        try {
            const response = await axios.post("http://65.0.183.78:8000/monthly-product-orders", { admin_id });
            const currentMonth = new Date().toISOString().slice(0, 7);
            const currentData = response.data.data.find((item) => item.month === currentMonth);
            setCurrentMonthOrders(currentData ? currentData.total_quantity : 0);
        } catch (error) {
            console.error("Error fetching monthly orders:", error);
        }
    };

    return (
        <div className="dashboard-container">
            <div className="dashboard-cards">
                <div className="dashboard-card card-sales-first">
                    <h3 className='today-heading'><FaBoxOpen className="today-icon" /> Total Products</h3>
                    <p>{summaryData?.total_products ?? "-"}</p>
                </div>
                <div className="dashboard-card card-sales-second">
                    <h3 className='today-heading'><SlPeople className="monthly-icon" />Total Customers</h3>
                    <p>{summaryData?.total_customers ?? "-"}</p>
                </div>
                <div className="dashboard-card card-sales-third">
                    <h3 className='today-heading'><FaBoxOpen className="yearly-icon" />Monthly Products Ordered</h3>
                    <p>{currentMonthOrders !== null ? `${currentMonthOrders}` : "Loading..."}</p>
                </div>
            </div>

            <div className="dashboard-tables">

                <div className="dashboard-top-buyers">
                    <h2>Top Buyers</h2>
                    <table className="dashboard-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Products Bought</th>
                            </tr>
                        </thead>
                        <tbody>
                            {topBuyers.slice(0, 5).map((buyer) => (
                                <tr key={buyer.customer_id}>
                                    <td>{buyer.name}</td>
                                    <td>{buyer.product_count}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {topBuyers.length > 5 && (
                        <button className="view-more-button" onClick={() => navigate("/top-buyers")}>
                                View More...
                        </button>
                    )}
                </div>


                {lowStockProducts.length > 0 && (
                    <div className="dashboard-low-stock">
                        <h2>Low Stock Products</h2>
                        <table className="dashboard-table">
                            <thead>
                                <tr>
                                    <th>Product Name</th>
                                    <th>Quantity</th>
                                </tr>
                            </thead>
                            <tbody>
                                {lowStockProducts.slice(0, 5).map((product) => (
                                    <tr key={product.product_id}>
                                        <td>{product.product_name}</td>
                                        <td>{product.quantity}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {lowStockProducts.length > 5 && (
                            <button className="view-more-button" onClick={() => navigate("/low-stock-products")}>
                                View More...
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
