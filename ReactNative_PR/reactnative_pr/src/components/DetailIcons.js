import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';


const DetailsIcon = (props) => {
    return(
        <View style={styles.container}>
            <View >
                <MaterialCommunityIcons name={props.name} color="gray" size={30} style={styles.star} />
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

export default DetailsIcon;