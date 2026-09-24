import React, {useState} from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import AuthScreen from '../components/AuthScreen';
import FormInput from '../components/FormInput';
import {useAuth} from '../context/AuthContext';
import {validateSignIn} from '../utils/auth';

const LogIn = ({navigation}) => {
  const {signIn} = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = async () => {
    const validationError = validateSignIn({email, password});

    if (validationError) {
      setError(validationError);
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      await signIn({email, password});
    } catch (signInError) {
      setError(signInError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthScreen
      title="Welcome back"
      subtitle="Log in to search hotels and manage your booking requests."
      navigation={navigation}
      footer={
        <View style={styles.footer}>
          <Text style={styles.footerText}>New to Hotel Booking?</Text>
          <TouchableOpacity
            accessibilityRole="button"
            onPress={() => navigation.navigate('SignUp')}
          >
            <Text style={styles.footerLink}>Create an account</Text>
          </TouchableOpacity>
        </View>
      }
    >
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
        onChangeText={(value) => {
          setEmail(value);
          setError('');
        }}
        returnKeyType="next"
      />
      <FormInput
        label="Password"
        icon="lock-outline"
        placeholder="Enter your password"
        secureTextEntry
        autoCapitalize="none"
        autoComplete="current-password"
        textContentType="password"
        value={password}
        onChangeText={(value) => {
          setPassword(value);
          setError('');
        }}
        returnKeyType="done"
        onSubmitEditing={handleLogin}
      />

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
        onPress={handleLogin}
      >
        {isSubmitting ? (
          <ActivityIndicator color="#FFFFFF" />
        ) : (
          <Text style={styles.submitText}>Log in</Text>
        )}
      </TouchableOpacity>
    </AuthScreen>
  );
};

const styles = StyleSheet.create({
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
    marginTop: 2,
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

export default LogIn;
