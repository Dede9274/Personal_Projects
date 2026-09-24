import React, {useState} from 'react';
import {StyleSheet, Text, TextInput, TouchableOpacity, View} from 'react-native';
import {MaterialCommunityIcons} from '@expo/vector-icons';

const FormInput = ({
  label,
  icon,
  secureTextEntry = false,
  inputRef,
  style,
  ...inputProps
}) => {
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const shouldHidePassword = secureTextEntry && !isPasswordVisible;

  return (
    <View style={[styles.field, style]}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.inputContainer}>
        <MaterialCommunityIcons
          name={icon}
          color="#667085"
          size={21}
          style={styles.icon}
        />
        <TextInput
          ref={inputRef}
          style={styles.input}
          placeholderTextColor="#98A2B3"
          secureTextEntry={shouldHidePassword}
          {...inputProps}
        />
        {secureTextEntry ? (
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={isPasswordVisible ? 'Hide password' : 'Show password'}
            style={styles.visibilityButton}
            onPress={() => setIsPasswordVisible((current) => !current)}
          >
            <MaterialCommunityIcons
              name={isPasswordVisible ? 'eye-off-outline' : 'eye-outline'}
              color="#667085"
              size={21}
            />
          </TouchableOpacity>
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  field: {
    width: '100%',
    marginBottom: 16,
  },
  label: {
    color: '#344054',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 7,
  },
  inputContainer: {
    minHeight: 52,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#D0D5DD',
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
  },
  icon: {
    marginLeft: 13,
  },
  input: {
    minWidth: 0,
    flex: 1,
    color: '#1D2939',
    fontSize: 16,
    paddingHorizontal: 11,
    paddingVertical: 13,
  },
  visibilityButton: {
    minWidth: 44,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default FormInput;
