import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './AdminCustomerReports.css';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { FcSalesPerformance } from "react-icons/fc";
import { PiHandCoinsBold } from "react-icons/pi";
import { GiCoins } from "react-icons/gi";
import { BsCoin } from "react-icons/bs";

const AdminCustomerReports = () => {
  const [adminId, setAdminId] = useState(null);
  const [summary, setSummary] = useState({ today: 0, month: 0, total: 0 });
  const [monthlyRevenue, setMonthlyRevenue] = useState({});
  const [topProducts, setTopProducts] = useState([]);
  const [orderStatusData, setOrderStatusData] = useState([]);
  const [error, setError] = useState('');
  const [reportYear, setReportYear] = useState(new Date().getFullYear());
  const maxAmount = Math.max(...Object.values(monthlyRevenue));
  const currentYear = new Date().getFullYear();

  const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444'];

  // Function to format amounts to currency
  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(amount);
  };

  useEffect(() => {
    const storedAdminId = sessionStorage.getItem('admin_id');
    if (!storedAdminId) {
      setError('Admin session expired. Please log in again.');
      return;
    }

    setAdminId(storedAdminId);

    fetchSalesSummary(storedAdminId);
    fetchMonthlyRevenue(storedAdminId);
    fetchTopProducts(storedAdminId);
    fetchOrderStatusSummary(storedAdminId);
  }, [reportYear]); // Dependency array includes reportYear to refetch when it changes

  const fetchSalesSummary = async (admin_id) => {
    try {
      const res = await axios.post('http://127.0.0.1:8000/report-sales-summary', { admin_id });
      if (res.data.status_code === 200) {
        setSummary({
          today: res.data.today_sales_amount,
          month: res.data.this_month_sales_amount,
          total: res.data.total_sales_amount
        });
      }
    } catch (err) {
      console.error('Error fetching sales summary', err);
    }
  };

  const fetchMonthlyRevenue = async (admin_id) => {
    try {
      const res = await axios.post('http://127.0.0.1:8000/report-monthly-revenue-by-year', {
        admin_id,
        year: reportYear
      });
      if (res.data.status_code === 200) {
        setMonthlyRevenue(res.data.monthly_revenue);
      }
    } catch (err) {
      console.error('Error fetching monthly revenue', err);
    }
  };

  const fetchTopProducts = async (admin_id) => {
    try {
      const res = await axios.post('http://127.0.0.1:8000/top-five-selling-products', { admin_id });
      if (res.data.status_code === 200) {
        setTopProducts(res.data.top_5_products);
      }
    } catch (err) {
      console.error('Error fetching top products', err);
    }
  };

  const fetchOrderStatusSummary = async (admin_id) => {
    try {
      const res = await axios.post('http://127.0.0.1:8000/order-status-summary', { admin_id });
      if (res.data.status_code === 200 && res.data.order_status_summary) {
        const data = res.data.order_status_summary;
        const transformed = Object.entries(data).map(([status, value]) => ({
          name: status.charAt(0).toUpperCase() + status.slice(1), // Capitalize first letter
          value: value
        }));
        setOrderStatusData(transformed);
      }
    } catch (err) {
      console.error('Error fetching order status summary', err);
    }
  };

  const handleYearChange = (event) => {
    setReportYear(event.target.value); // Update the year and fetch data for that year
  };

  if (error) {
    return <div className="dashboard"><h2>{error}</h2></div>;
  }

  const barHeightScalingFactor = maxAmount ? 300 / maxAmount : 0; // scale the bars relative to the max amount

  return (
    <div className="dashboard-reports">
      <h2 className='sales-reports'>Sales Reports</h2>

      <div className="summary-cards">
        <div className="card-sales-first"><h3 className='today-heading'><BsCoin className="today-icon" />Today</h3> <p>{formatAmount(summary.today)}</p></div>
        <div className="card-sales-second"><h3 className='today-heading'><PiHandCoinsBold className="monthly-icon" />Monthly</h3><p>{formatAmount(summary.month)}</p></div>
        <div className="card-sales-third"><h3 className='today-heading'><GiCoins className="yearly-icon" />Yearly</h3><p>{formatAmount(summary.total)}</p></div>
      </div>

      <div className="charts-status">
        <div className="chart-box">
          <h3>Yearly Revenue ({reportYear})</h3>
          <select onChange={handleYearChange} value={reportYear}>
            {/* {[currentYear, currentYear - 1, currentYear - 2].map(year => (
              <option key={year} value={year}>{year}</option>
            ))} */}
            {[currentYear, currentYear - 1].map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          <div className="bar-chart">
            {Object.entries(monthlyRevenue).map(([month, amount]) => (
              <div key={month} className="bar-wrapper">
                <div className="bar" data-amount={`₹${amount}`} style={{ '--bar-height': `${amount * barHeightScalingFactor}px` }}></div>
                <label>{month.slice(0, 3)}</label>
              </div>
            ))}
          </div>
        </div>

        <div className="pie-chart-box">
          <h3 >Order Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={orderStatusData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {orderStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="product-boxes">
        <div className="top-products">
          <h3>Top 5 Products</h3>
          <ul>
            {topProducts.map(p => (
              <li key={p.product_id}>{p.product_name}  {p.total_sold}</li>
            ))}
          </ul>
        </div>

        <div className="bottom-products">
          <h3>Bottom 5 Products</h3>
          <p>Coming soon...</p>
        </div>
      </div>
    </div>
  );
};

export default AdminCustomerReports;

