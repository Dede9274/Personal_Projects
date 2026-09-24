import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import Home from '../screens/Home';
import SignUp from '../screens/SignUp';
import Welcome from '../screens/Welcome';
import Booking from '../screens/Booking';
import BookingConfirmation from '../screens/BookingConfirmation';
import Single from '../screens/Single';
import LogIn from '../screens/LogIn';
import AppLoading from '../components/AppLoading';
import {useAuth} from '../context/AuthContext';

const Stack = createStackNavigator();

const screenOptions = {
  headerShown: false,
  cardStyle: {backgroundColor: '#FFFFFF'},
};

const StackNavigator = () => {
  const {user, isLoading} = useAuth();

  if (isLoading) {
    return <AppLoading />;
  }

  return (
    <Stack.Navigator
      key={user ? 'authenticated' : 'guest'}
      screenOptions={screenOptions}
    >
      {user ? (
        <>
          <Stack.Screen name="Home" component={Home} />
          <Stack.Screen name="Single" component={Single} />
          <Stack.Screen name="Booking" component={Booking} />
          <Stack.Screen name="BookingConfirmation" component={BookingConfirmation} />
        </>
      ) : (
        <>
          <Stack.Screen name="Welcome" component={Welcome} />
          <Stack.Screen name="LogIn" component={LogIn} />
          <Stack.Screen name="SignUp" component={SignUp} />
        </>
      )}
    </Stack.Navigator>
  );
};

export default StackNavigator;
