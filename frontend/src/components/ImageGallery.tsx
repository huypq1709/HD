import React from "react";
export function ImageGallery({
  images
}) {
  return <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
      {images.map((image, index) => <div key={index} className="relative h-48 overflow-hidden rounded-lg">
          <img src={image.url} alt={image.alt} className="w-full h-full object-cover transform hover:scale-105 transition-transform duration-300" />
        </div>)}
    </div>;
}