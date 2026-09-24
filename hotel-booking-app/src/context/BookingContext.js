import React, {createContext, useCallback, useContext, useMemo, useState} from 'react';

const BookingContext = createContext(null);

export const BookingProvider = ({children}) => {
  const [bookings, setBookings] = useState([]);

  const submitBooking = useCallback((request) => {
    const booking = {
      ...request,
      id: `HB-${Date.now().toString().slice(-6)}`,
      status: 'Pending',
      requestedAt: new Date().toISOString(),
    };

    setBookings((current) => [booking, ...current]);
    return booking;
  }, []);

  const value = useMemo(
    () => ({bookings, submitBooking}),
    [bookings, submitBooking]
  );

  return (
    <BookingContext.Provider value={value}>
      {children}
    </BookingContext.Provider>
  );
};

export const useBookings = () => {
  const context = useContext(BookingContext);

  if (!context) {
    throw new Error('useBookings must be used inside BookingProvider.');
  }

  return context;
};
