import React from 'react';
import {View, Text, StyleSheet, Image, TouchableOpacity, Button} from 'react-native';
import StarIcon from '../components/StarIcon';
import Single from '../screens/Single';

const Hotel = ({navigation, hotel}) => {
    
    return(
            
            <View style={styles.cardContainer}>

           
                <View style={styles.imgContainer}>
                    <Image source={{uri: `${hotel.image}`}} resizeMode="cover" style={styles.img} /> 
                </View>
            
                <View style={styles.textContainer}>
                    <Text style={styles.name}>{hotel.name}</Text>
                    <Text style={styles.location}>{hotel.location}</Text>
                    <View style={styles.ovrRating}>
                        <Text style={styles.rating}>{hotel.rating}</Text>
                        <View style={styles.starRating}>
                            <StarIcon name="star"/>
                            <Text style={styles.nrRating}>{hotel.nrRating}</Text>
                        </View>
                    </View>
                    <Text style={styles.price}>{hotel.price}</Text>
                </View>
            </View>
        
    )
 
}

const styles = StyleSheet.create({
    cardContainer:{
        flexDirection:'row',
        width:'100%',
        height:170
    },
    img:{
        width:100,
        height:'100%',
        borderRadius: 10,
        
    },
    imgContainer:
    {
        padding:2,
        
    },
    name: {
        paddingTop: 3,
        fontSize: 18,
        paddingLeft: 10
    },
    
    starRating:{
        display: 'flex',
        flexDirection: 'row',
        paddingLeft: 3,
        
    },
    nrRating:{
        color: 'gray'
    },
    location:{
        color:'gray',
        paddingHorizontal:10,
        paddingTop: 5
    },
    price:{
        justifyContent: 'flex-end',
        paddingLeft: 150,
        top: 17,
        fontSize: 25,
        color: '#3CA6B9'
    },
    ovrRating:{
        top:65,
        paddingHorizontal:5
    },
    rating:{
        color:'gray'
    },
    btn: {
        padding:0
    }
})

export default Hotel;