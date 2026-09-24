import React from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import data from '../data/data.json';
import BackIcon from '../components/BackiIcon';
import StarIcon from '../components/StarIcon';
import DetailsIcon from '../components/DetailIcons';

const AMENITIES = [
  {key: 'wifi', label: 'Wi-Fi', icon: 'wifi'},
  {key: 'ac', label: 'Air conditioning', icon: 'fan'},
  {key: 'gym', label: 'Gym', icon: 'dumbbell'},
  {key: 'spa', label: 'Spa', icon: 'waves'},
  {key: 'tv', label: 'TV', icon: 'television'},
];

const Single = ({navigation, route}) => {
  const {width, height} = useWindowDimensions();
  const id = route.params?.singleID;
  const selectedHotel = data.find((hotel) => hotel.id === id);
  const heroHeight = Math.min(Math.max(width * 0.52, 260), Math.min(height * 0.58, 520));

  if (!selectedHotel) {
    return (
      <SafeAreaView style={styles.missingContainer}>
        <Text style={styles.missingTitle}>Hotel not found</Text>
        <TouchableOpacity style={styles.primaryButton} onPress={() => navigation.goBack()}>
          <Text style={styles.primaryButtonText}>Go back</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const amenities = AMENITIES.filter((amenity) => selectedHotel[amenity.key]);

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.page}>
          <View style={[styles.hero, {height: heroHeight}]}>
            <Image
              source={{uri: selectedHotel.image}}
              resizeMode="cover"
              style={styles.image}
            />
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="Go back"
              style={styles.backButton}
              onPress={() => navigation.goBack()}
            >
              <BackIcon color="#1D2939" size={30} />
            </TouchableOpacity>
          </View>

          <View style={styles.card}>
            <View style={styles.titleRow}>
              <View style={styles.titleGroup}>
                <Text style={styles.name}>{selectedHotel.name}</Text>
                <Text style={styles.location}>{selectedHotel.location}</Text>
              </View>
              <View style={styles.priceGroup}>
                <Text style={styles.price}>{selectedHotel.price}</Text>
                <Text style={styles.perNight}>per night</Text>
              </View>
            </View>

            <View style={styles.ratingRow}>
              <StarIcon />
              <Text style={styles.rating}>{selectedHotel.nrRating}</Text>
              <Text style={styles.ratingLabel}>{selectedHotel.rating}</Text>
            </View>

            <Text style={styles.sectionTitle}>About this hotel</Text>
            <Text style={styles.description}>{selectedHotel.description}</Text>

            <Text style={styles.sectionTitle}>Amenities</Text>
            <View style={styles.amenities}>
              {amenities.map((amenity) => (
                <View key={amenity.key} style={styles.amenity}>
                  <DetailsIcon name={amenity.icon} />
                  <Text style={styles.amenityText}>{amenity.label}</Text>
                </View>
              ))}
            </View>

            <TouchableOpacity
              accessibilityRole="button"
              style={styles.primaryButton}
              onPress={() => navigation.navigate('Booking', {hotelId: selectedHotel.id})}
            >
              <Text style={styles.primaryButtonText}>Book now</Text>
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
    backgroundColor: '#F2F6F7',
  },
  scrollContent: {
    alignItems: 'center',
    paddingBottom: 24,
  },
  page: {
    width: '100%',
    maxWidth: 1000,
  },
  hero: {
    position: 'relative',
    width: '100%',
    minHeight: 260,
    backgroundColor: '#DCE6E8',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  backButton: {
    position: 'absolute',
    top: 16,
    left: 16,
    width: 46,
    height: 46,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 23,
    backgroundColor: 'rgba(255, 255, 255, 0.92)',
  },
  card: {
    width: '94%',
    maxWidth: 900,
    alignSelf: 'center',
    borderRadius: 24,
    backgroundColor: '#FFFFFF',
    marginTop: -30,
    padding: 24,
    shadowColor: '#102A30',
    shadowOpacity: 0.1,
    shadowRadius: 18,
    shadowOffset: {width: 0, height: 8},
    elevation: 4,
  },
  titleRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  titleGroup: {
    flex: 1,
    minWidth: 210,
    paddingRight: 14,
  },
  name: {
    color: '#1D2939',
    fontSize: 28,
    lineHeight: 34,
    fontWeight: '800',
  },
  location: {
    color: '#667085',
    lineHeight: 20,
    marginTop: 5,
  },
  priceGroup: {
    alignItems: 'flex-end',
    marginTop: 2,
  },
  price: {
    color: '#27899A',
    fontSize: 27,
    fontWeight: '800',
  },
  perNight: {
    color: '#98A2B3',
    fontSize: 12,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 15,
  },
  rating: {
    color: '#344054',
    fontWeight: '700',
    marginLeft: 5,
  },
  ratingLabel: {
    color: '#667085',
    marginLeft: 7,
  },
  sectionTitle: {
    color: '#1D2939',
    fontSize: 18,
    fontWeight: '700',
    marginTop: 27,
    marginBottom: 9,
  },
  description: {
    color: '#475467',
    fontSize: 15,
    lineHeight: 23,
  },
  amenities: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -5,
  },
  amenity: {
    minWidth: 120,
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 10,
    backgroundColor: '#F5FAFB',
    paddingHorizontal: 12,
    paddingVertical: 11,
    margin: 5,
  },
  amenityText: {
    color: '#475467',
    marginLeft: 8,
  },
  primaryButton: {
    width: '100%',
    maxWidth: 520,
    minHeight: 55,
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 11,
    backgroundColor: '#27899A',
    marginTop: 30,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
  },
  missingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    padding: 24,
  },
  missingTitle: {
    color: '#1D2939',
    fontSize: 22,
    fontWeight: '700',
  },
});

export default Single;
