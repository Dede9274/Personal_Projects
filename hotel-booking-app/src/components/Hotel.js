import React from 'react';
import {Image, StyleSheet, Text, View} from 'react-native';
import StarIcon from './StarIcon';

const Hotel = ({hotel, vertical = false}) => (
  <View style={[styles.card, vertical && styles.verticalCard]}>
    <Image
      accessibilityLabel={hotel.name}
      source={{uri: hotel.image}}
      resizeMode="cover"
      style={[styles.image, vertical && styles.verticalImage]}
    />

    <View style={styles.content}>
      <View>
        <Text numberOfLines={2} style={styles.name}>{hotel.name}</Text>
        <Text numberOfLines={2} style={styles.location}>{hotel.location}</Text>
      </View>

      <View style={styles.footer}>
        <View>
          <Text style={styles.ratingLabel}>{hotel.rating}</Text>
          <View style={styles.ratingRow}>
            <StarIcon />
            <Text style={styles.ratingNumber}>{hotel.nrRating}</Text>
          </View>
        </View>
        <View style={styles.priceGroup}>
          <Text style={styles.price}>{hotel.price}</Text>
          <Text style={styles.perNight}>per night</Text>
        </View>
      </View>
    </View>
  </View>
);

const styles = StyleSheet.create({
  card: {
    minHeight: 166,
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
  },
  verticalCard: {
    minHeight: 330,
    flexDirection: 'column',
  },
  image: {
    width: 120,
    alignSelf: 'stretch',
    backgroundColor: '#E8EEF0',
  },
  verticalImage: {
    width: '100%',
    height: 175,
    alignSelf: 'auto',
  },
  content: {
    minWidth: 0,
    flex: 1,
    justifyContent: 'space-between',
    padding: 14,
  },
  name: {
    color: '#1D2939',
    fontSize: 18,
    lineHeight: 23,
    fontWeight: '700',
  },
  location: {
    color: '#667085',
    lineHeight: 19,
    marginTop: 5,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    marginTop: 14,
  },
  ratingLabel: {
    color: '#667085',
    fontSize: 12,
    marginBottom: 3,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingNumber: {
    color: '#344054',
    fontWeight: '600',
    marginLeft: 4,
  },
  priceGroup: {
    alignItems: 'flex-end',
    marginLeft: 10,
  },
  price: {
    color: '#27899A',
    fontSize: 23,
    fontWeight: '800',
  },
  perNight: {
    color: '#98A2B3',
    fontSize: 11,
    marginTop: 1,
  },
});

export default Hotel;
