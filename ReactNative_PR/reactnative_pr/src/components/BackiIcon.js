import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';


const BackIcon = (props) => {
    return(
        <View >
            <View  style={styles.container}>
                <MaterialCommunityIcons name={props.name} color="gray" size={40} style={styles.star} />
            </View>
            <Text >{props.iconText}</Text>
        </View>

    );

}

const styles = StyleSheet.create ({
  container:{
    top:11,
    paddingHorizontal: 5
  }
})

export default BackIcon;