import React from "react";
import Slider from "react-slick";
import carouselImage from "../../../assets/images/carousel-banner.png";
import "./CustomerCarousel.css";

const carouselItems = [
  {
    image: carouselImage,
    alt: "Drone Banner 1",
  },
  {
    image: carouselImage,
    alt: "Drone Banner 2",
  },
  {
    image: carouselImage,
    alt: "Drone Banner 3",
  },
];

const CarouselLanding = () => {
  const settings = {
    dots: true,
    infinite: true,
    speed: 800,
    slidesToShow: 1,
    slidesToScroll: 1,
    autoplay: true,
    autoplaySpeed: 5000,
    arrows: true,
  };

  return (
    <div className="carousel-wrapper container">
      <Slider {...settings}>
        {carouselItems.map((item, index) => (
          <div key={index} className="carousel-slide">
            <img src={item.image} alt={item.alt} className="carousel-img" />
          </div>
        ))}
      </Slider>
    </div>
  );
};

export default CarouselLanding;
