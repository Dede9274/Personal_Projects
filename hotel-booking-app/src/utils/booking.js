const parseGuestCount = (value) => {
  if (!/^\d+$/.test(String(value).trim())) {
    return null;
  }

  return Number(value);
};

export const validateBooking = ({hotelId, checkIn, checkOut, adults, children}) => {
  const adultCount = parseGuestCount(adults);
  const childCount = parseGuestCount(children);

  if (!hotelId) return 'Please select a hotel before booking.';
  if (!checkIn || !checkOut) return 'Choose both a check-in and check-out date.';
  if (checkOut <= checkIn) return 'Check-out must be after check-in.';
  if (adultCount === null || adultCount < 1) return 'At least one adult is required.';
  if (childCount === null) return 'Children must be a whole number of zero or more.';

  return null;
};

export const createBookingRequest = ({hotelId, checkIn, checkOut, adults, children}) => ({
  hotelId,
  checkIn,
  checkOut,
  adults: Number(adults),
  children: Number(children),
});
