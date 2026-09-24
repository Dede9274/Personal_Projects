import React, {useMemo, useState} from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import moment from 'moment';
import BackIcon from '../components/BackiIcon';
import Calendar from '../components/CalendarPicker';
import data from '../data/data.json';
import {useBookings} from '../context/BookingContext';
import {createBookingRequest, validateBooking} from '../utils/booking';

const Booking = ({navigation, route}) => {
  const {width} = useWindowDimensions();
  const hotelId = route.params?.hotelId;
  const hotel = useMemo(
    () => data.find((item) => item.id === hotelId),
    [hotelId]
  );
  const {submitBooking} = useBookings();
  const [checkIn, setCheckIn] = useState(null);
  const [checkOut, setCheckOut] = useState(null);
  const [adults, setAdults] = useState('2');
  const [children, setChildren] = useState('0');
  const [error, setError] = useState('');
  const stackGuests = width < 440;

  const handleCheckIn = (date) => {
    setCheckIn(date);
    setError('');

    if (checkOut && checkOut <= date) {
      setCheckOut(null);
    }
  };

  const handleSubmit = () => {
    const formValues = {hotelId, checkIn, checkOut, adults, children};
    const validationError = validateBooking(formValues);

    if (validationError) {
      setError(validationError);
      return;
    }

    const booking = submitBooking(createBookingRequest(formValues));
    navigation.replace('BookingConfirmation', {booking});
  };

  if (!hotel) {
    return (
      <SafeAreaView style={styles.missingContainer}>
        <Text style={styles.missingTitle}>No hotel selected</Text>
        <Text style={styles.missingCopy}>
          Open a hotel first so your booking request has the correct destination.
        </Text>
        <TouchableOpacity style={styles.primaryButton} onPress={() => navigation.navigate('Home')}>
          <Text style={styles.primaryButtonText}>Browse hotels</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.page}>
          <View style={styles.header}>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="Go back"
              style={styles.backButton}
              onPress={() => navigation.goBack()}
            >
              <BackIcon />
            </TouchableOpacity>
            <Text style={styles.title}>Book a room</Text>
            <View style={styles.headerSpacer} />
          </View>

          <View style={styles.hotelSummary}>
            <Image source={{uri: hotel.image}} style={styles.hotelImage} />
            <View style={styles.hotelSummaryText}>
              <Text numberOfLines={2} style={styles.hotelName}>{hotel.name}</Text>
              <Text numberOfLines={2} style={styles.hotelLocation}>{hotel.location}</Text>
              <Text style={styles.hotelPrice}>{hotel.price} / night</Text>
            </View>
          </View>

          <View style={styles.formCard}>
            <Text style={styles.label}>Check-in date</Text>
            <Calendar
              value={checkIn}
              minDate={moment().startOf('day')}
              onDateChange={handleCheckIn}
            />

            <View style={styles.divider} />

            <Text style={styles.label}>Check-out date</Text>
            <Calendar
              value={checkOut}
              minDate={
                checkIn
                  ? moment(checkIn, 'YYYY-MM-DD').add(1, 'day')
                  : moment().startOf('day').add(1, 'day')
              }
              onDateChange={(date) => {
                setCheckOut(date);
                setError('');
              }}
            />

            <View style={[styles.guestRow, stackGuests && styles.stackedGuestRow]}>
              <View style={styles.guestField}>
                <Text style={styles.label}>Adults</Text>
                <TextInput
                  accessibilityLabel="Number of adults"
                  keyboardType="number-pad"
                  style={styles.guestInput}
                  value={adults}
                  onChangeText={(value) => {
                    setAdults(value.replace(/[^0-9]/g, ''));
                    setError('');
                  }}
                  placeholder="2"
                  placeholderTextColor="#98A2B3"
                />
              </View>
              <View style={[styles.guestField, !stackGuests && styles.childrenField]}>
                <Text style={styles.label}>Children</Text>
                <TextInput
                  accessibilityLabel="Number of children"
                  keyboardType="number-pad"
                  style={styles.guestInput}
                  value={children}
                  onChangeText={(value) => {
                    setChildren(value.replace(/[^0-9]/g, ''));
                    setError('');
                  }}
                  placeholder="0"
                  placeholderTextColor="#98A2B3"
                />
              </View>
            </View>

            {error ? (
              <Text accessibilityRole="alert" style={styles.error}>
                {error}
              </Text>
            ) : null}

            <TouchableOpacity
              accessibilityRole="button"
              style={styles.primaryButton}
              onPress={handleSubmit}
            >
              <Text style={styles.primaryButtonText}>Request booking</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5FAFB',
  },
  scrollContent: {
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 30,
  },
  page: {
    width: '100%',
    maxWidth: 760,
  },
  header: {
    minHeight: 68,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerSpacer: {
    width: 44,
  },
  title: {
    color: '#1D2939',
    fontSize: 22,
    fontWeight: '800',
  },
  hotelSummary: {
    flexDirection: 'row',
    padding: 12,
    borderRadius: 14,
    backgroundColor: '#E7F6F8',
    marginBottom: 14,
  },
  hotelImage: {
    width: 88,
    height: 88,
    flexShrink: 0,
    borderRadius: 10,
    backgroundColor: '#DCE6E8',
  },
  hotelSummaryText: {
    minWidth: 0,
    flex: 1,
    marginLeft: 12,
    justifyContent: 'center',
  },
  hotelName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D2939',
  },
  hotelLocation: {
    color: '#667085',
    marginTop: 3,
  },
  hotelPrice: {
    color: '#27899A',
    fontWeight: '700',
    marginTop: 6,
  },
  formCard: {
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 18,
  },
  label: {
    color: '#344054',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 2,
  },
  divider: {
    height: 1,
    backgroundColor: '#E4E7EC',
    marginVertical: 14,
  },
  guestRow: {
    flexDirection: 'row',
    marginTop: 12,
  },
  stackedGuestRow: {
    flexDirection: 'column',
  },
  guestField: {
    flex: 1,
    marginTop: 10,
  },
  childrenField: {
    marginLeft: 14,
  },
  guestInput: {
    height: 52,
    borderColor: '#D0D5DD',
    marginTop: 8,
    borderWidth: 1,
    paddingHorizontal: 12,
    borderRadius: 9,
    fontSize: 17,
    color: '#1D2939',
    backgroundColor: '#FFFFFF',
  },
  error: {
    color: '#B42318',
    backgroundColor: '#FEF3F2',
    borderRadius: 8,
    marginTop: 18,
    padding: 12,
  },
  primaryButton: {
    width: '100%',
    maxWidth: 540,
    minHeight: 55,
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 11,
    backgroundColor: '#27899A',
    marginTop: 24,
  },
  primaryButtonText: {
    fontSize: 17,
    color: '#FFFFFF',
    fontWeight: '700',
  },
  missingContainer: {
    flex: 1,
    padding: 30,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
  },
  missingTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1D2939',
  },
  missingCopy: {
    color: '#667085',
    textAlign: 'center',
    lineHeight: 21,
    marginTop: 10,
  },
});

export default Booking;
