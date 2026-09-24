import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import MapView, {Marker} from 'react-native-maps';
import data from '../data/data.json';
import Hotel from '../components/Hotel';
import Icon from '../components/Icon';
import MapSortIcon from '../components/MapSortIcon';
import SearchBar from '../components/SearchBar';
import {filterAndSortHotels} from '../utils/hotels';
import {useAuth} from '../context/AuthContext';

const SORT_OPTIONS = [
  {key: 'recommended', label: 'Recommended'},
  {key: 'priceLow', label: 'Price: low to high'},
  {key: 'priceHigh', label: 'Price: high to low'},
  {key: 'rating', label: 'Guest rating'},
];

const Home = ({navigation}) => {
  const {width} = useWindowDimensions();
  const {user, signOut} = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('recommended');
  const [sortVisible, setSortVisible] = useState(false);
  const [viewMode, setViewMode] = useState('list');
  const mapRef = useRef(null);
  const isGrid = width >= 760;
  const stackControls = width < 390;

  const visibleHotels = useMemo(
    () => filterAndSortHotels(data, searchQuery, sortBy),
    [searchQuery, sortBy]
  );

  const selectedSort = SORT_OPTIONS.find((option) => option.key === sortBy);

  const openHotel = useCallback(
    (hotel) => navigation.navigate('Single', {singleID: hotel.id}),
    [navigation]
  );

  const fitMapToResults = useCallback(() => {
    if (!mapRef.current || visibleHotels.length === 0) {
      return;
    }

    if (visibleHotels.length === 1) {
      const {latitude, longitude} = visibleHotels[0].coordinates;
      mapRef.current.animateToRegion(
        {latitude, longitude, latitudeDelta: 5, longitudeDelta: 5},
        350
      );
      return;
    }

    mapRef.current.fitToCoordinates(
      visibleHotels.map((hotel) => hotel.coordinates),
      {
        edgePadding: {top: 60, right: 45, bottom: 60, left: 45},
        animated: true,
      }
    );
  }, [visibleHotels]);

  useEffect(() => {
    if (viewMode !== 'map') {
      return undefined;
    }

    const timer = setTimeout(fitMapToResults, 150);
    return () => clearTimeout(timer);
  }, [fitMapToResults, viewMode]);

  const renderHotel = ({item}) => (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={`View ${item.name}`}
      style={[styles.itemContainer, isGrid && styles.gridItem]}
      onPress={() => openHotel(item)}
    >
      <Hotel hotel={item} vertical={isGrid} />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom', 'left', 'right']}>
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <View style={styles.topHeader}>
            <View style={styles.brandRow}>
              <View style={styles.iconContainer}>
                <Icon name="bed-king-outline" />
              </View>
              <View style={styles.headingGroup}>
                <Text style={styles.greeting}>Hello, {user.firstName}</Text>
                <Text style={styles.title}>Find your best hotel</Text>
              </View>
            </View>

            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="Log out"
              style={styles.logoutButton}
              onPress={signOut}
            >
              <MaterialCommunityIcons name="logout" color="#475467" size={21} />
              {width >= 430 ? <Text style={styles.logoutText}>Log out</Text> : null}
            </TouchableOpacity>
          </View>

          <SearchBar value={searchQuery} onChangeText={setSearchQuery} />
          <View style={[styles.buttonContainer, stackControls && styles.stackedButtons]}>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="Choose hotel sort order"
              style={styles.actionButton}
              onPress={() => setSortVisible(true)}
            >
              <MapSortIcon name="sort-bool-ascending-variant" />
              <Text numberOfLines={1} style={styles.actionText}>
                {selectedSort.label}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={viewMode === 'map' ? 'Show hotel list' : 'Show hotels on map'}
              style={[
                styles.actionButton,
                stackControls ? styles.stackedMapButton : styles.mapButton,
              ]}
              onPress={() => setViewMode((current) => current === 'list' ? 'map' : 'list')}
            >
              <MapSortIcon name={viewMode === 'map' ? 'format-list-bulleted' : 'map-outline'} />
              <Text style={styles.actionText}>{viewMode === 'map' ? 'List' : 'Map'}</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.resultCount}>
            {visibleHotels.length} {visibleHotels.length === 1 ? 'hotel' : 'hotels'} found
          </Text>
        </View>
      </View>

      {viewMode === 'list' ? (
        <FlatList
          key={isGrid ? 'grid' : 'list'}
          data={visibleHotels}
          numColumns={isGrid ? 2 : 1}
          keyExtractor={(hotel) => String(hotel.id)}
          renderItem={renderHotel}
          columnWrapperStyle={isGrid ? styles.gridRow : undefined}
          contentContainerStyle={[
            styles.hotelList,
            visibleHotels.length === 0 && styles.emptyList,
          ]}
          keyboardShouldPersistTaps="handled"
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <MaterialCommunityIcons name="bed-empty" color="#98A2B3" size={42} />
              <Text style={styles.emptyTitle}>No hotels found</Text>
              <Text style={styles.emptyCopy}>Try another hotel name or destination.</Text>
            </View>
          }
        />
      ) : (
        <View style={styles.mapContainer}>
          {visibleHotels.length > 0 ? (
            <MapView
              ref={mapRef}
              style={styles.map}
              onMapReady={fitMapToResults}
              initialRegion={{
                latitude: 45,
                longitude: 12,
                latitudeDelta: 35,
                longitudeDelta: 35,
              }}
            >
              {visibleHotels.map((hotel) => (
                <Marker
                  key={hotel.id}
                  coordinate={hotel.coordinates}
                  title={hotel.name}
                  description={`${hotel.location} · ${hotel.price}`}
                  onCalloutPress={() => openHotel(hotel)}
                />
              ))}
            </MapView>
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyTitle}>No hotels to map</Text>
              <Text style={styles.emptyCopy}>Clear or change your search to see locations.</Text>
            </View>
          )}
          {visibleHotels.length > 0 ? (
            <View style={styles.mapHint}>
              <Text style={styles.mapHintText}>Tap a marker, then its callout, for details.</Text>
            </View>
          ) : null}
        </View>
      )}

      <Modal
        animationType="fade"
        transparent
        visible={sortVisible}
        onRequestClose={() => setSortVisible(false)}
      >
        <Pressable style={styles.modalBackdrop} onPress={() => setSortVisible(false)}>
          <Pressable style={styles.sortSheet} onPress={() => {}}>
            <Text style={styles.sortTitle}>Sort hotels</Text>
            {SORT_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.key}
                accessibilityRole="radio"
                accessibilityState={{checked: sortBy === option.key}}
                style={styles.sortOption}
                onPress={() => {
                  setSortBy(option.key);
                  setSortVisible(false);
                }}
              >
                <Text
                  style={[
                    styles.sortOptionText,
                    sortBy === option.key && styles.sortOptionSelected,
                  ]}
                >
                  {option.label}
                </Text>
                {sortBy === option.key ? (
                  <MaterialCommunityIcons name="check" color="#27899A" size={21} />
                ) : null}
              </TouchableOpacity>
            ))}
          </Pressable>
        </Pressable>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    backgroundColor: '#FFFFFF',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E4E7EC',
  },
  headerContent: {
    width: '100%',
    maxWidth: 1100,
    alignSelf: 'center',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 11,
  },
  topHeader: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  brandRow: {
    minWidth: 0,
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    width: 48,
    height: 48,
    flexShrink: 0,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 14,
    backgroundColor: '#E7F6F8',
    marginRight: 11,
  },
  headingGroup: {
    minWidth: 0,
    flex: 1,
  },
  greeting: {
    color: '#667085',
    fontSize: 13,
  },
  title: {
    color: '#1D2939',
    fontSize: 21,
    fontWeight: '800',
  },
  logoutButton: {
    minHeight: 44,
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 9,
    paddingHorizontal: 10,
    marginLeft: 8,
  },
  logoutText: {
    color: '#475467',
    fontWeight: '600',
    marginLeft: 6,
  },
  buttonContainer: {
    width: '100%',
    flexDirection: 'row',
    marginTop: 10,
  },
  stackedButtons: {
    flexDirection: 'column',
  },
  actionButton: {
    minHeight: 46,
    flex: 1,
    borderWidth: 1,
    borderColor: '#D0D5DD',
    borderRadius: 9,
    paddingHorizontal: 12,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  mapButton: {
    marginLeft: 10,
  },
  stackedMapButton: {
    marginTop: 8,
  },
  actionText: {
    color: '#475467',
    marginLeft: 7,
    flexShrink: 1,
  },
  resultCount: {
    width: '100%',
    color: '#667085',
    fontSize: 13,
    marginTop: 9,
  },
  hotelList: {
    width: '100%',
    maxWidth: 1100,
    alignSelf: 'center',
    paddingHorizontal: 10,
    paddingTop: 14,
    paddingBottom: 30,
  },
  emptyList: {
    flexGrow: 1,
  },
  gridRow: {
    alignItems: 'stretch',
  },
  itemContainer: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E4E7EC',
    borderRadius: 12,
    marginHorizontal: 6,
    marginBottom: 12,
    overflow: 'hidden',
    backgroundColor: '#FFFFFF',
  },
  gridItem: {
    flexBasis: '47%',
    maxWidth: '50%',
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 30,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D2939',
    marginTop: 10,
  },
  emptyCopy: {
    color: '#667085',
    textAlign: 'center',
    marginTop: 8,
  },
  mapContainer: {
    flex: 1,
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  mapHint: {
    position: 'absolute',
    alignSelf: 'center',
    left: 20,
    right: 20,
    bottom: 18,
    maxWidth: 600,
    backgroundColor: 'rgba(29, 41, 57, 0.9)',
    borderRadius: 9,
    padding: 10,
  },
  mapHintText: {
    color: '#FFFFFF',
    textAlign: 'center',
    fontSize: 13,
  },
  modalBackdrop: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  sortSheet: {
    width: '100%',
    maxWidth: 560,
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingHorizontal: 24,
    paddingTop: 22,
    paddingBottom: 34,
  },
  sortTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 10,
    color: '#1D2939',
  },
  sortOption: {
    minHeight: 52,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E4E7EC',
  },
  sortOptionText: {
    color: '#475467',
    fontSize: 16,
  },
  sortOptionSelected: {
    color: '#27899A',
    fontWeight: '700',
  },
});

export default Home;
