import React from 'react';
import { View, Text, Button, TouchableOpacity, Image, StyleSheet, TextInput} from 'react-native';
import BackIcon from '../components/BackiIcon';
import OtherIcon from '../components/OtherIcon';

const LogIn = ({navigation}) => {
    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={()=> navigation.goBack()}>
                    <BackIcon name='chevron-left' />
                </TouchableOpacity>    
                <Text style={styles.title}>Log Into Your Account</Text>
            </View>
            <View style={styles.inputContainer}>
                <View style={styles.otherInputs}>
                    <TextInput style={styles.emailInput} placeholder='E-mail' />
                    <TextInput style={styles.passwordInput} placeholder='Password' />
                    <TouchableOpacity style={styles.btn} onPress={() => navigation.navigate('Home')}><Text style={{alignSelf:'center', fontSize:18, color:'white'}}>Log In</Text></TouchableOpacity>
                </View>
                <View style={styles.bottomContainer}>
                    <Text style={{color:'gray'}}>------------------------------------OR----------------------------------</Text>

                </View>
                <View style={styles.bottomContainer}>
                    <View style={styles.other}>
                        <TouchableOpacity style={styles.otherBtn}><OtherIcon name='google' color='#F75D59'/><Text style={{alignSelf:'center', padding: 5, color: 'gray'}}>Continue with Google</Text></TouchableOpacity>
                        <TouchableOpacity style={styles.otherBtn}><OtherIcon name='apple' /><Text style={{alignSelf:'center', padding: 5, color: 'gray'}}>Continue with Apple</Text></TouchableOpacity>
                        <TouchableOpacity style={styles.otherBtn}><OtherIcon name='facebook' color='blue'/><Text style={{alignSelf:'center', padding: 5, color: 'gray'}}>Continue with Facebook</Text></TouchableOpacity>

                    </View>
                </View>
            </View>

        </View>
    );
}

const styles = StyleSheet.create ({
    header:{
        flexDirection: 'row',
        alignContent:'center',
        marginTop: 30
    },
    title:{
        alignSelf:'center',
        fontSize: 22,
        paddingLeft: 75,
      color: '#3CA6B9'
    },
   
    emailInput:{
        padding: 10,
        height: 50,
        width: '98%',
        borderWidth: 1.5,
        borderColor: '#D3D3D3',
        borderRadius: 10,
        padding:10
    },
    otherInputs:{
        paddingHorizontal: 24,
        marginTop: 15
    },
    passwordInput:{
        padding: 10,
        height: 50,
        width: '98%',
        borderWidth: 1.5,
        borderColor: '#D3D3D3',
        borderRadius: 10,
        padding:10,
        marginTop: 12
    },
    btn:{
        marginTop: 25,
        width: '98%',
        height:55,
        backgroundColor: '#3CA6B9',
        borderRadius: 10,
        flexDirection: 'row',
        justifyContent: 'center',
        
    },
    bottomContainer:{
        flexDirection: 'row',
        justifyContent: 'center',
        marginTop: 50
    },
    otherBtn:{
        direction:'flex',
        flexDirection:'row',
        marginTop: 2,
        borderColor: 'gray',
        borderWidth: 1,
        borderRadius: 10,
        width: 295,
        height: 50,
        padding: 10,
        justifyContent: 'center',
        marginBottom: 13
    }

})

export default LogIn;