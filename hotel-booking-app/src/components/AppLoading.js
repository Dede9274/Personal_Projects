import React from 'react';
import {ActivityIndicator, StyleSheet, Text, View} from 'react-native';

const AppLoading = () => (
  <View style={styles.container}>
    <ActivityIndicator color="#27899A" size="large" />
    <Text style={styles.text}>Preparing your stay…</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
  },
  text: {
    color: '#667085',
    fontSize: 15,
    marginTop: 14,
  },
});

export default AppLoading;
