import React from 'react';
import {View, Button, Text, Image, FlatList, ScrollView, StyleSheet, Header, TouchableOpacity} from 'react-native';
import data from '../data/data.json';
import Hotel from '../components/Hotel';
import Icon from '../components/Icon';
import MapSortIcon from '../components/MapSortIcon';
import SearchBar from '../components/SearchBar';
import { useNavigation } from '@react-navigation/native';


class Home extends React.Component {

   

    constructor(){
        super();
        this.state = {
            hotels:[]
        }
    }

    componentDidMount(){
        this.setState({
            hotels: data
        })
    }
    
    render(navigation){
     
        return( 
           <ScrollView> 
            <View style={styles.Container}>
                    <View style={styles.header}>
                        <View style={styles.topHeader}>
                            <View style={styles.iconContainer}>
                                <Icon name="bed-king" />
                            </View>
                            <View style={styles.titleContainer}>
                                <Text style={styles.title}>Find your best Hotel</Text>
                            </View>
                        </View>
                        <View style={styles.bottomHeader}>
                            <SearchBar />
                            <View style={styles.btnContainer}>
                                <TouchableOpacity style={styles.sortbtn}><MapSortIcon name="sort-bool-ascending-variant"/><Text style={{color:'gray'}}>Sort</Text></TouchableOpacity>
                                <TouchableOpacity style={styles.Mapbtn}><MapSortIcon name="map-outline"/><Text style={{color:'gray'}}>Map</Text></TouchableOpacity>
                            </View>
                        </View>
                    </View>
                        <View style={styles.hotelsContainer}>
                            <FlatList data={this.state.hotels}
                                
                                renderItem = {({item, navigation}) => (
                                    <View style={styles.itemContainer}>
                                            <TouchableOpacity
                onPress={() => this.props.navigation.navigate('Single', {singleID: item.id})}>
                                            <Hotel hotel={item}/>
                                            </TouchableOpacity>
                                     </View>                                )}
                                 
                                
                            />                     
                        </View>
                </View>                    
            </ScrollView>                
        )
    }

}

const styles = StyleSheet.create ({
    Container:{
        backgroundColor: 'white'
    },  
    hotelsContainer:{
        marginTop: 50,
        paddingStart: 15,
        paddingEnd: 15
         
    },
    header: {
        marginTop:50,
        
            
    },
    topHeader:{
        flexDirection: 'row',
        justifyContent: 'flex-end',
        marginBottom: 0
    },
   
    title:{
        fontSize: 21,
        fontWeight: 'bold',
        paddingRight: 15
  
    },
    itemContainer:
    {
        borderWidth: 0.1,
        borderColor: 'gray',
        borderRadius: 8,
        marginBottom:10
    },
    bottomHeader:{
        alignItems: 'center'
    },
    btnContainer:{
        flexDirection:'row',
        marginTop: 10,
        
    },
    sortbtn:{
        width: '43%',
        borderWidth: 0.2,
        borderColor: 'gray',
        borderRadius: 6,
        paddingHorizontal:35,
        marginRight: 10,
        alignItems: 'center',
        flexDirection: 'row',
        justifyContent: 'center'
        
    },
    Mapbtn:{
        width: '43%',
        borderWidth: 0.2,
        borderColor: 'gray',
        borderRadius: 6,
        paddingHorizontal:35,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center'
      
        
    }
})

export default Home;