import Slider from "rc-slider";
import "rc-slider/assets/index.css";

const { Range } = Slider; // Fix for import

const PriceSlider = ({ minPrice, maxPrice, setMinPrice, setMaxPrice }) => {
    const handleSliderChange = (values) => {
        setMinPrice(values[0]);
        setMaxPrice(values[1]);
    };

    return (
        <div className="price-filter-slider">
            <h4 className="price-label">PRICE</h4>

            <Range
                min={0}
                max={10000}
                step={100}
                value={[minPrice, maxPrice]}
                onChange={handleSliderChange}
                trackStyle={[{ backgroundColor: "#ff2e74", height: 4 }]}
                handleStyle={[
                    { backgroundColor: "#fff", borderColor: "#ff2e74", height: 16, width: 16 },
                    { backgroundColor: "#fff", borderColor: "#ff2e74", height: 16, width: 16 }
                ]}
            />

            <div className="price-range-values">
                ₹{minPrice} - ₹{maxPrice}
            </div>
        </div>
    );
};

export default PriceSlider;
