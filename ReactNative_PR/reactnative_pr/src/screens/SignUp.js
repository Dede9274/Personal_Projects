import React, {Component} from 'react';
import { View, Text, Button, TouchableOpacity, Image, StyleSheet, TextInput} from 'react-native';
import BackIcon from '../components/BackiIcon';
import OtherIcon from '../components/OtherIcon';

class SignUp extends Component{

    constructor(props){
        super(props)
        this.state = {
            TextInput_User_Name: '',
            TextInput_User_Surname: '',
            TextInput_User_Email: '',
            TextInput_User_Password: ''
        }
    }

    insertUserData = () =>{ 
        fetch('http://192.168.2.104/hotels_db/insertStudentData.php',{
            method:'POST',
            headers:{
                'Accept':'application/json', 
                'Content-Type':'application/json'
            },
            body: JSON.stringify({
                account_name : this.state.TextInput_User_Name,
                account_surname : this.state.TextInput_User_Surname,
                account_email : this.state.TextInput_User_Email, 
                account_password : this.state.TextInput_User_Password
            })

        }).then((response) => response.text())
            .then((responseJson) => {
                Alert.alert(responseJson)
            }).catch((error) => {
                console.log(error); 
            });
    } 
 
    render(navigation) {
        return (
            <View style={styles.container}>
                <View style={styles.header}>
                    <TouchableOpacity onPress={()=> this.props.navigation.goBack()}>
                        <BackIcon name='chevron-left' />
                    </TouchableOpacity>    
                    <Text style={styles.title}>Create an Account</Text>
                </View>
                <View style={styles.inputContainer}>
                    <View style={styles.nameSurname}>
                        <TextInput style={styles.nameInput} placeholder='First Name' 
                            onChangeText={TextInputValue => this.setState({TextInput_User_Name: TextInputValue})}
                            />
                        <TextInput style={styles.surnameInput} placeholder='Last Name'
                            onChangeText={TextInputValue => this.setState({TextInput_User_Surname: TextInputValue})}
                            />
                    </View>
                    <View style={styles.otherInputs}>
                        <TextInput style={styles.emailInput} placeholder='E-mail' 
                            onChangeText={TextInputValue => this.setState({TextInput_User_Email: TextInputValue})}
                        />
                        <TextInput style={styles.passwordInput} placeholder='Password' 
                            onChangeText={TextInputValue => this.setState({TextInput_User_Password: TextInputValue})}
                        />
                        <TouchableOpacity style={styles.btn} onPress={this.insertUserData}><Text style={{alignSelf:'center', fontSize:18, color:'white'}}>Sign Up</Text></TouchableOpacity>
                    </View>
                    <View style={styles.bottomContainer}>
                    <Text style={{color:'gray'}}>------------------------------------OR----------------------------------</Text>

                </View>
                <View style={styles.bottomContainer}>
                    <View style={styles.other}>
                        <TouchableOpacity style={styles.otherBtn}><OtherIcon name='google' color='#F75D59'/><Text style={{alignSelf:'center', padding: 5, color: 'gray'}}>Continue with Google</Text></TouchableOpacity>
                        <TouchableOpacity style={styles.otherBtn}><OtherIcon name='apple' color='#4C4E52'/><Text style={{alignSelf:'center', padding: 5, color: 'gray'}}>Continue with Apple</Text></TouchableOpacity>
                        <TouchableOpacity style={styles.otherBtn}><OtherIcon name='facebook' color='#4267B2'/><Text style={{alignSelf:'center', padding: 5, color: 'gray'}}>Continue with Facebook</Text></TouchableOpacity>

                    </View>
                </View>
                </View>

            </View>
        );
    }
}

const styles = StyleSheet.create ({
    header:{
        flexDirection: 'row',
        alignContent:'center',
        marginTop: 30
    },
    title:{
        alignSelf:'center',
        fontSize: 22,
        paddingLeft: 110,
      color: '#3CA6B9'
    },
    nameSurname:{
        marginTop: 20,
        flexDirection: 'row',
        paddingHorizontal: 23
    },
    nameInput:{
        height: 50,
        width: '35%',
        borderWidth: 1.5,
        borderColor: '#D3D3D3',
        borderRadius: 10,
        marginRight: 10,
        padding:10
       
    },
    surnameInput:{
        height: 50,
        width: '60%',
        borderWidth: 1.5,
        borderColor: '#D3D3D3',
        borderRadius: 10,
        padding:10
    },
    emailInput:{
        padding: 10,
        height: 50,
        width: '98%',
        borderWidth: 1.5,
        borderColor: '#D3D3D3',
        borderRadius: 10,
        padding:10
    },
    otherInputs:{
        paddingHorizontal: 24,
        marginTop: 15
    },
    passwordInput:{
        padding: 10,
        height: 50,
        width: '98%',
        borderWidth: 1.5,
        borderColor: '#D3D3D3',
        borderRadius: 10,
        padding:10,
        marginTop: 12
    },
    btn:{
        marginTop: 25,
        width: '98%',
        height:55,
        backgroundColor: '#3CA6B9',
        borderRadius: 10,
        flexDirection: 'row',
        justifyContent: 'center',
        
    },
    bottomContainer:{
        flexDirection: 'row',
        justifyContent: 'center',
        marginTop: 50
    },
    otherBtn:{
        direction:'flex',
        flexDirection:'row',
        marginTop: 2,
        borderColor: 'gray',
        borderWidth: 1,
        borderRadius: 10,
        width: 295,
        height: 50,
        padding: 10,
        justifyContent: 'center',
        marginBottom: 13
    }

})

export default SignUp;