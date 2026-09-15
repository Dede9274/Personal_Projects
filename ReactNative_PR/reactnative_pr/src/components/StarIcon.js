import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';


const StarIcon = (props) => {
    return(
        <View style={styles.container}>
            <View >
                <MaterialCommunityIcons name={props.name} color="orange" size={20} style={styles.star} />
            </View>
            <Text >{props.iconText}</Text>
        </View>

    );

}

const styles = StyleSheet.create ({
    container:{
        flexDirection:'row',
        alignItems:'center'
    }
})

export default StarIcon;