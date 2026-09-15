import React from 'react';
import {View, StyleSheet, Text, Image, TouchableOpacity} from 'react-native';
import { color } from 'react-native-reanimated';

const Welcome = ({navigation}) => {
    return (
        <View style={styles.container}>
            <View style={styles.imgContainer}>
                <Image style={styles.img} source={require('../../assets/sea.jpg')} />
            </View>
            <View style={styles.body}>
    
                <Text style={{color:'#3CA6B9', fontSize:25, alignSelf: 'center', bottom:50}}>Book your Dream Vacation</Text>
                <Text style={{color:'gray', fontSize:15, fontWeight:'bold', alignSelf:'center', bottom: 30}}>Find the best and most comfortable hotel for you</Text>
                <View style={styles.btns}>
                    <TouchableOpacity onPress={() => navigation.navigate('LogIn')} style={styles.logIn}><Text style={{color:'gray', alignSelf:'center'}}>Log In</Text></TouchableOpacity>
                    <TouchableOpacity onPress={() => navigation.navigate('SignUp')} style={styles.signUp} ><Text style={{color:'white',alignSelf:'center'}}>Sign Up</Text></TouchableOpacity>
                </View>
            </View>
        </View>
    )
}

const styles = StyleSheet.create({ 
    imgContainer: {
        padding:15,
        paddingTop:35,
        paddingBottom:0
    },
    img:{
        width:'100%',
        height: '85%',
        borderRadius: 30
    },
    body:{
        marginTop:0
       
    },
    btns:{
        flexDirection:'row',
        paddingHorizontal:60
    },
    logIn:{
        marginRight: 35,
        width: '40%',
        flexDirection: 'row',
        justifyContent: 'center' 
    },  
    signUp:{
        width: '60%',
        height: 50,
        backgroundColor: '#3CA6B9',
        borderRadius: 10,
        flexDirection: 'row',
        justifyContent: 'center'
    }
})

export default Welcome;  