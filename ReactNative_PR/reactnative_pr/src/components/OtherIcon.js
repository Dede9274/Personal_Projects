import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';


const OtherIcon = (props) => {
    return(
        <View style={styles.container}>
            <View >
            <MaterialCommunityIcons name={props.name} color={props.color} size={30}  />
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

export default OtherIcon;