import * as React from 'react';
import { Searchbar } from 'react-native-paper';
import {View, StyleSheet, Text} from 'react-native';

const SearchBar = () => {
  const [searchQuery, setSearchQuery] = React.useState('');

  const onChangeSearch = query => setSearchQuery(query);

  return (
    <Searchbar
    style={styles.searchBar}
      placeholder="Location or Name"
      iconColor='#3CA6B9'
      placeholderTextColor={'gray'}
      onChangeText={onChangeSearch}
      value={searchQuery}
    />
  );
};

const styles = StyleSheet.create ({
    searchBar:{
        width: '90%',
        backgroundColor:'white',
        marginTop: 1,
        borderRadius: 8
    }
})

export default SearchBar;