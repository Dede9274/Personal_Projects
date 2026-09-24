import React from 'react';
import {StyleSheet} from 'react-native';
import {Searchbar} from 'react-native-paper';

const SearchBar = ({value, onChangeText}) => (
  <Searchbar
    accessibilityLabel="Search hotels by name or location"
    style={styles.searchBar}
    inputStyle={styles.input}
    placeholder="Search by location or hotel"
    iconColor="#27899A"
    placeholderTextColor="#98A2B3"
    onChangeText={onChangeText}
    value={value}
  />
);

const styles = StyleSheet.create({
  searchBar: {
    width: '100%',
    minHeight: 52,
    borderRadius: 11,
    backgroundColor: '#F8FAFB',
    borderWidth: 1,
    borderColor: '#E4E7EC',
    elevation: 0,
  },
  input: {
    color: '#1D2939',
    fontSize: 16,
  },
});

export default SearchBar;
