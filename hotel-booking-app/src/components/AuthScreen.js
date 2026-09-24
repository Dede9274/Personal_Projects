import React from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';

const AuthScreen = ({title, subtitle, navigation, children, footer}) => {
  const {width} = useWindowDimensions();
  const horizontalPadding = width < 380 ? 16 : 24;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={[
            styles.scrollContent,
            {paddingHorizontal: horizontalPadding},
          ]}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.form}>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="Go back"
              style={styles.backButton}
              onPress={() => navigation.goBack()}
            >
              <MaterialCommunityIcons name="chevron-left" color="#344054" size={32} />
              <Text style={styles.backText}>Back</Text>
            </TouchableOpacity>

            <View style={styles.brandIcon}>
              <MaterialCommunityIcons name="bed-king-outline" color="#27899A" size={34} />
            </View>
            <Text style={styles.title}>{title}</Text>
            <Text style={styles.subtitle}>{subtitle}</Text>

            {children}
            {footer}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5FAFB',
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 28,
  },
  form: {
    width: '100%',
    maxWidth: 520,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    padding: 24,
    shadowColor: '#102A30',
    shadowOpacity: 0.08,
    shadowRadius: 20,
    shadowOffset: {width: 0, height: 8},
    elevation: 3,
  },
  backButton: {
    minHeight: 44,
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: -8,
    marginBottom: 18,
  },
  backText: {
    color: '#475467',
    fontSize: 15,
  },
  brandIcon: {
    width: 58,
    height: 58,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E7F6F8',
    marginBottom: 18,
  },
  title: {
    color: '#1D2939',
    fontSize: 28,
    lineHeight: 34,
    fontWeight: '800',
  },
  subtitle: {
    color: '#667085',
    fontSize: 15,
    lineHeight: 22,
    marginTop: 8,
    marginBottom: 24,
  },
});

export default AuthScreen;
