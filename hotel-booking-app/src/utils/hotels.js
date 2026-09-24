const normalize = (value) => String(value || '').trim().toLowerCase();

export const getHotelPrice = (hotel) =>
  Number(String(hotel.price).replace(/[^\d]/g, '')) || 0;

export const getHotelRating = (hotel) =>
  Number(String(hotel.nrRating).replace(',', '.')) || 0;

export const filterAndSortHotels = (hotels, query, sortBy) => {
  const normalizedQuery = normalize(query);
  const filteredHotels = hotels.filter((hotel) =>
    normalize(`${hotel.name} ${hotel.location}`).includes(normalizedQuery)
  );

  return [...filteredHotels].sort((first, second) => {
    switch (sortBy) {
      case 'priceLow':
        return getHotelPrice(first) - getHotelPrice(second);
      case 'priceHigh':
        return getHotelPrice(second) - getHotelPrice(first);
      case 'rating':
        return getHotelRating(second) - getHotelRating(first);
      default:
        return first.id - second.id;
    }
  });
};
