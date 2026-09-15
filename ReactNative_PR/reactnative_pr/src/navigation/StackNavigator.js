import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import Home from '../screens/Home';
import SignUp from '../screens/SignUp';
import Welcome from '../screens/Welcome';
import Booking from '../screens/Booking';
import Single from '../screens/Single';
import LogIn from '../screens/LogIn';

const Stack = createStackNavigator();

const screenOptionStyle = {
    
       headerShown: false
   
}


const StackNavigator = ({navigation}) => { 
    return(
        <Stack.Navigator screenOptions={screenOptionStyle}>
            <Stack.Screen name="Welcome" component={Welcome} />
              <Stack.Screen name="Home" component={Home} />
            <Stack.Screen name="Booking" component={Booking} />
            <Stack.Screen name="SignUp" component={SignUp} />
            <Stack.Screen name="Single" component={Single} />
           <Stack.Screen name="LogIn" component={LogIn}/>
            
            
        </Stack.Navigator>
    );
}



export default StackNavigator;