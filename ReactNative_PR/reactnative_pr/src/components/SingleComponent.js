import React from 'react';
import {View, Text, StyleSheet, Image, TouchableOpacity} from 'react-native';

const SingleComponent = ({single}) => {
    return(
        <View style={styles.container}>
            <View style={styles.imgContainer}>
                <Image source={{uri: `${single.image}`}} resizeMode="cover" style={styles.img} /> 
            </View>
            <View style={styles.cardContainer}>
                <View style={styles.header}>
                    <View style={styles.headerName}>
                        <Text>{single.name}</Text>
                        <Text>{single.location}</Text>
                    </View>       
                    <Text>{single.nrRating}</Text>
                    <Text>{single.price}</Text>
                </View>
                <View styles={styles.descriptionHolder}>
                    <Text>{single.description}</Text>
                </View>
                <View style={styles.iconsContainer}>
                    <Text>{single.wifi}</Text>
                    <Text>{single.ac}</Text>
                    <Text>{single.gym}</Text>
                    <Text>{single.spa}</Text>
                </View>
            </View>
        </View>
    )
}

const styles = StyleSheet.create({

})

export default SingleComponent;