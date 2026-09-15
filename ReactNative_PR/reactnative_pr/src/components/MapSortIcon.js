import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';


const MapSortIcon = (props) => {
    return(
        <View >
            <View  style={styles.container}>
                <MaterialCommunityIcons name={props.name} color="#3CA6B9" size={20} style={styles.star} />
            </View>
            <Text >{props.iconText}</Text>
        </View>

    );

}

const styles = StyleSheet.create ({
    container: {
        top: 10,
        right: 2
    }
})

export default MapSortIcon;