import React, {useState} from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import AuthScreen from '../components/AuthScreen';
import FormInput from '../components/FormInput';
import {useAuth} from '../context/AuthContext';
import {validateSignUp} from '../utils/auth';

const SignUp = ({navigation}) => {
  const {width} = useWindowDimensions();
  const {signUp} = useAuth();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const useTwoColumns = width >= 560;

  const updateField = (setter) => (value) => {
    setter(value);
    setError('');
  };

  const handleSignUp = async () => {
    const values = {
      firstName,
      lastName,
      email,
      password,
      confirmPassword,
    };
    const validationError = validateSignUp(values);

    if (validationError) {
      setError(validationError);
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      await signUp(values);
    } catch (signUpError) {
      setError(signUpError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthScreen
      title="Create your account"
      subtitle="Save your session and continue directly to your hotel search."
      navigation={navigation}
      footer={
        <View style={styles.footer}>
          <Text style={styles.footerText}>Already have an account?</Text>
          <TouchableOpacity
            accessibilityRole="button"
            onPress={() => navigation.navigate('LogIn')}
          >
            <Text style={styles.footerLink}>Log in</Text>
          </TouchableOpacity>
        </View>
      }
    >
      <View style={useTwoColumns ? styles.nameRow : null}>
        <FormInput
          style={useTwoColumns ? styles.nameField : null}
          label="First name"
          icon="account-outline"
          placeholder="First name"
          autoCapitalize="words"
          autoComplete="given-name"
          textContentType="givenName"
          value={firstName}
          onChangeText={updateField(setFirstName)}
          returnKeyType="next"
        />
        <FormInput
          style={useTwoColumns ? styles.lastNameField : null}
          label="Last name"
          icon="account-outline"
          placeholder="Last name"
          autoCapitalize="words"
          autoComplete="family-name"
          textContentType="familyName"
          value={lastName}
          onChangeText={updateField(setLastName)}
          returnKeyType="next"
        />
      </View>

      <FormInput
        label="Email address"
        icon="email-outline"
        placeholder="you@example.com"
        autoCapitalize="none"
        autoCorrect={false}
        autoComplete="email"
        keyboardType="email-address"
        textContentType="emailAddress"
        value={email}
        onChangeText={updateField(setEmail)}
        returnKeyType="next"
      />
      <FormInput
        label="Password"
        icon="lock-outline"
        placeholder="At least 8 characters"
        secureTextEntry
        autoCapitalize="none"
        autoComplete="new-password"
        textContentType="newPassword"
        value={password}
        onChangeText={updateField(setPassword)}
        returnKeyType="next"
      />
      <FormInput
        label="Confirm password"
        icon="lock-check-outline"
        placeholder="Repeat your password"
        secureTextEntry
        autoCapitalize="none"
        autoComplete="new-password"
        textContentType="newPassword"
        value={confirmPassword}
        onChangeText={updateField(setConfirmPassword)}
        returnKeyType="done"
        onSubmitEditing={handleSignUp}
      />

      <Text style={styles.passwordHint}>
        Use 8 or more characters with at least one letter and one number.
      </Text>

      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}

      <TouchableOpacity
        accessibilityRole="button"
        accessibilityState={{disabled: isSubmitting}}
        disabled={isSubmitting}
        style={[styles.submitButton, isSubmitting && styles.buttonDisabled]}
        onPress={handleSignUp}
      >
        {isSubmitting ? (
          <ActivityIndicator color="#FFFFFF" />
        ) : (
          <Text style={styles.submitText}>Create account</Text>
        )}
      </TouchableOpacity>
    </AuthScreen>
  );
};

const styles = StyleSheet.create({
  nameRow: {
    flexDirection: 'row',
  },
  nameField: {
    width: 'auto',
    flex: 1,
    marginRight: 7,
  },
  lastNameField: {
    width: 'auto',
    flex: 1,
    marginLeft: 7,
  },
  passwordHint: {
    color: '#667085',
    fontSize: 12,
    lineHeight: 18,
    marginTop: -4,
    marginBottom: 16,
  },
  error: {
    color: '#B42318',
    backgroundColor: '#FEF3F2',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  submitButton: {
    minHeight: 54,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
    backgroundColor: '#27899A',
  },
  buttonDisabled: {
    opacity: 0.65,
  },
  submitText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
  },
  footer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 24,
  },
  footerText: {
    color: '#667085',
    marginRight: 5,
  },
  footerLink: {
    color: '#27899A',
    fontWeight: '700',
  },
});

export default SignUp;
