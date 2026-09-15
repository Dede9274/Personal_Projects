import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';


const Icon = (props) => {
    return(
        <View >
            <View style={styles.container}>
                <MaterialCommunityIcons name={props.name} color="#3CA6B9" size={40}/>
            </View>
            <Text >{props.iconText}</Text>
        </View>

    );

}


const styles = StyleSheet.create({
    container:{
        right: 95,
        top : -6
    }
})

export default Icon;