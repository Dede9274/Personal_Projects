import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import moment from 'moment';
import data from '../data/data.json';

const DetailRow = ({label, value}) => (
  <View style={styles.detailRow}>
    <Text style={styles.detailLabel}>{label}</Text>
    <Text style={styles.detailValue}>{value}</Text>
  </View>
);

const BookingConfirmation = ({navigation, route}) => {
  const booking = route.params?.booking;
  const hotel = data.find((item) => item.id === booking?.hotelId);

  if (!booking || !hotel) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.title}>Booking details unavailable</Text>
        <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Home')}>
          <Text style={styles.buttonText}>Return home</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const nights = moment(booking.checkOut).diff(moment(booking.checkIn), 'days');

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.content}>
          <View style={styles.iconCircle}>
            <MaterialCommunityIcons name="check" size={48} color="#FFFFFF" />
          </View>
          <Text style={styles.title}>Booking requested</Text>
          <Text style={styles.subtitle}>
            Your request for {hotel.name} is saved for this app session.
          </Text>

          <View style={styles.card}>
            <DetailRow label="Reference" value={booking.id} />
            <DetailRow label="Hotel" value={hotel.name} />
            <DetailRow
              label="Check-in"
              value={moment(booking.checkIn).format('MMM D, YYYY')}
            />
            <DetailRow
              label="Check-out"
              value={moment(booking.checkOut).format('MMM D, YYYY')}
            />
            <DetailRow label="Stay" value={`${nights} ${nights === 1 ? 'night' : 'nights'}`} />
            <DetailRow
              label="Guests"
              value={`${booking.adults} adult${booking.adults === 1 ? '' : 's'}, ${booking.children} child${booking.children === 1 ? '' : 'ren'}`}
            />
            <DetailRow label="Status" value={booking.status} />
          </View>

          <Text style={styles.note}>
            This demo stores booking requests locally. Connect submitBooking to a reservation API for production.
          </Text>

          <TouchableOpacity
            accessibilityRole="button"
            style={styles.button}
            onPress={() =>
              navigation.reset({
                index: 0,
                routes: [{name: 'Home'}],
              })
            }
          >
            <Text style={styles.buttonText}>Explore more hotels</Text>
          </TouchableOpacity>
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
    flexGrow: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 18,
    paddingVertical: 30,
  },
  content: {
    width: '100%',
    maxWidth: 560,
    alignItems: 'center',
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#FFFFFF',
  },
  iconCircle: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#27899A',
    marginBottom: 22,
  },
  title: {
    color: '#1D2939',
    fontSize: 25,
    fontWeight: '800',
    textAlign: 'center',
  },
  subtitle: {
    color: '#667085',
    textAlign: 'center',
    lineHeight: 21,
    marginTop: 8,
    marginBottom: 24,
  },
  card: {
    width: '100%',
    borderRadius: 14,
    paddingHorizontal: 18,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E4E7EC',
  },
  detailRow: {
    minHeight: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E4E7EC',
  },
  detailLabel: {
    flexShrink: 0,
    color: '#667085',
  },
  detailValue: {
    minWidth: 0,
    flex: 1,
    color: '#1D2939',
    fontWeight: '600',
    textAlign: 'right',
    marginLeft: 15,
  },
  note: {
    color: '#667085',
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
    marginTop: 16,
  },
  button: {
    width: '100%',
    minHeight: 55,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#27899A',
    marginTop: 24,
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 17,
  },
});

export default BookingConfirmation;
