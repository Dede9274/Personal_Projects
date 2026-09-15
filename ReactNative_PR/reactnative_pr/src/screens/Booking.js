import React from 'react';
import {View, TouchableOpacity, StyleSheet, Text, Image} from 'react-native';
import { TextInput , ScrollView} from 'react-native-gesture-handler';
import BackIcon from '../components/BackiIcon';
import Calendar from '../components/CalendarPicker';



const Booking = ({navigation}) => {
    return(
       <ScrollView >
        <View style={styles.container}>
            <View style={styles.header}>
            <TouchableOpacity onPress={()=> navigation.goBack()}>
                    <BackIcon name='chevron-left' />
                </TouchableOpacity>    
                <Text style={styles.title}>Book a room</Text>
            </View>
            <View style={styles.body}>
                <Text style={{color: '#3CA6B9', paddingHorizontal:20, paddingTop:15, fontSize: 17}}>Check-in Date</Text> 
                <Calendar />
                <Text style={{color: '#3CA6B9', paddingHorizontal:20, paddingTop:15, fontSize: 17, marginTop:20}}>Check-out date</Text>
                <Calendar />
                <Text style={{color: '#3CA6B9', paddingHorizontal:20, paddingTop:15, fontSize: 17}}>Number of Adults</Text> 
                <TextInput   keyboardType = 'numeric' style={styles.adults} placeholder='....' />
                <Text style={{color: '#3CA6B9', paddingHorizontal:20, paddingTop:15, fontSize: 17}}>Number of Children</Text> 
                <TextInput  keyboardType = 'numeric' style={styles.kids} placeholder='....' />
                <View style={{direction: 'flex', alignContent:'center'}}>
                    <TouchableOpacity style={styles.btn} ><Text 
                     style={{alignSelf:'center', fontSize:18, color:'white',}}>Request Booking</Text></TouchableOpacity>
                </View>
            </View>
        </View>
        </ScrollView>
    )


}

const styles = StyleSheet.create({
    container:{
       backgroundColor: 'white'
    },
    header:{
        flexDirection: 'row',
        alignContent:'center',
        marginTop: 30
    },
    title:{
        alignSelf:'center',
        fontSize: 22,
        paddingLeft: 160,
      color: '#3CA6B9'
    },
    adults: {
        width: '75%',
        height: 50,
        borderColor: 'gray',
        margin: 25 ,
        borderWidth:0.2,
        padding: 7,
        borderRadius: 7,
        
    },
    kids: {
        fontSize:17,
        padding:7,
        width: '75%',
        height: 50,
        borderColor: 'gray',
        margin: 25 ,
        borderWidth:0.2,
        borderRadius: 7,

    },
    btn:{
        alignSelf:'center',
        marginVertical: 25,
        width: '90%',
        height:55,
        backgroundColor: '#3CA6B9',
        borderRadius: 10,
        flexDirection: 'row',
        justifyContent: 'center',
    },
    body:{
        flexDirection: 'column',
        alignContent: 'center'
    }
})

export default Booking;