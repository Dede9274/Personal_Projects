import 'react-native-gesture-handler';
import React from 'react';
import {StyleSheet} from 'react-native';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import {NavigationContainer} from '@react-navigation/native';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {SQLiteProvider} from 'expo-sqlite';
import StackNavigator from './src/navigation/StackNavigator';
import {AuthProvider} from './src/context/AuthContext';
import {BookingProvider} from './src/context/BookingContext';
import {initializeDatabase} from './src/database/database';

export default function App() {
  return (
    <GestureHandlerRootView style={styles.container}>
      <SafeAreaProvider>
        <SQLiteProvider
          databaseName="hotel-booking.db"
          onInit={initializeDatabase}
        >
          <AuthProvider>
            <BookingProvider>
              <NavigationContainer>
                <StackNavigator />
              </NavigationContainer>
            </BookingProvider>
          </AuthProvider>
        </SQLiteProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
