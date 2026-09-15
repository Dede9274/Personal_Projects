import React from 'react';
import {View, StyleSheet, Text, TouchableOpacity, Image, Button} from 'react-native';
import { FlatList, ScrollView } from 'react-native-gesture-handler';
import data from '../data/data.json';
import SingleComponent from '../components/SingleComponent';
import BackIcon from '../components/BackiIcon';
import StarIcon from '../components/StarIcon';
import DetailsIcon from '../components/DetailIcons';

const Single = ({navigation, route}) =>{
    const id = route.params.singleID;
    console.log(id);
    const selectedHotel = data.find((element) => {return id == element.id})
    return(
      
        <View style={styles.container}>
            <View style={styles.topheader}>
            <TouchableOpacity onPress={()=> navigation.goBack()}>
                    <BackIcon name='chevron-left' />
                </TouchableOpacity>    
            </View>
            <View style={styles.imgContainer}>
                <Image source={{uri: `${selectedHotel.image}`}} resizeMode="cover" style={styles.img} /> 
            </View>
            <View style={styles.cardContainer}>
                <View style={styles.header}>
                    <View style={styles.headerName}>
                        <View >
                              <Text style={{fontSize:25}}>{selectedHotel.name}</Text>
                        </View>
                        
                            <Text style={styles.price}>{selectedHotel.price}</Text>
                        
                    </View>  
                   </View>
                    <Text style={{marginLeft:5, color: 'gray'}}>{selectedHotel.location}</Text>
                    <View style={styles.starRating}>
                        <StarIcon name='star' />     
                        <Text>{selectedHotel.nrRating}</Text>    
                    </View>
                   
               
                <View styles={styles.descriptionHolder}>
                   
                    <Text style={{fontSize:14}}>{selectedHotel.description}</Text>
                </View>
                
                <View style={styles.iconsContainer}>
                    <View style={styles.iconBox1}><DetailsIcon name='wifi'/><Text style={styles.icon}>Wifi</Text></View> 
                    <View style={styles.iconBox}><DetailsIcon name='fan'/><Text style={styles.icon}>AC</Text></View>
                     <View style={styles.iconBox}><DetailsIcon name='dumbbell'/><Text style={styles.icon}>Gym</Text></View>
                     <View style={styles.iconBox}><DetailsIcon name='waves'/><Text style={styles.icon}>Spa</Text></View>
                     <View style={styles.iconBox}><DetailsIcon name='television'/><Text style={styles.icon}>TV</Text></View>
                 </View>
                <View style={{direction:'flex', alignItems:'center'}}>
                <TouchableOpacity style={styles.btn} onPress={() => navigation.navigate('Booking')}><Text 
                 style={{alignSelf:'center', fontSize:18, color:'white'}}>Book Now</Text></TouchableOpacity>

             </View>
                </View>
                </View>
       
    )
    
    
}

const styles= StyleSheet.create({
    img:{
        width:'100%',
        height: '70%',
        bottom:60
    },
    
    cardContainer:{
        backgroundColor: 'white',
        borderTopRightRadius: 40,
        borderTopLeftRadius:40,
        bottom: 460,
        borderColor: 'white',
        borderWidth: 1,
        padding: 22
        
      
    },
    btn:{
        marginTop: 25,
        width: '90%',
        height:55,
        backgroundColor: '#3CA6B9',
        borderRadius: 10,
        flexDirection: 'row',
        justifyContent: 'center',
    },
  
    starRating:{
        marginLeft: 1,
        marginTop:2,
        marginBottom:15,
        display: 'flex',
        flexDirection: 'row',
        paddingLeft: 3,
        alignItems: 'center'
        
    },
    iconsContainer:{
        display:'flex',
        flexDirection:'row',
        marginTop:35,
        marginBottom: 15
    },
   
    price:{
        bottom: 3,
        marginLeft: 80,
        fontSize: 28,
        color: '#3CA6B9',
    },
    icon:{
        color: 'gray'
    },
    
    iconBox:{
        justifyContent:'center',
        marginHorizontal: 17,
        width:35,
        height:32,
        borderRadius:15,
        justifyContent: 'center',
        alignItems:'center',
   
        
    },
    iconBox1:{
        justifyContent:'center',
        marginRight: 15,
        width:35,
        height:32,
        borderRadius:15,
        justifyContent: 'center',
        alignItems:'center',
   
        
    },
    headerName:{
        flexDirection: 'row',
        
    }

})

export default Single;