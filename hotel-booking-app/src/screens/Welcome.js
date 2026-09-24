import React from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';

const Welcome = ({navigation}) => {
  const {width, height} = useWindowDimensions();
  const isWide = width >= 800;
  const imageHeight = isWide
    ? Math.min(Math.max(height - 80, 440), 680)
    : Math.min(Math.max(height * 0.48, 280), 480);

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={[styles.shell, isWide && styles.wideShell]}>
          <View
            style={[
              styles.imageContainer,
              {height: imageHeight},
              isWide && styles.wideImageContainer,
            ]}
          >
            <Image
              accessibilityLabel="Coastal hotel destination"
              source={require('../../assets/sea.jpg')}
              resizeMode="cover"
              style={styles.image}
            />
            <View style={styles.imageBadge}>
              <MaterialCommunityIcons name="map-marker-radius-outline" size={20} color="#FFFFFF" />
              <Text style={styles.imageBadgeText}>Discover your next stay</Text>
            </View>
          </View>

          <View style={[styles.body, isWide && styles.wideBody]}>
            <View style={styles.brand}>
              <MaterialCommunityIcons name="bed-king-outline" color="#27899A" size={34} />
            </View>
            <Text style={styles.eyebrow}>HOTEL BOOKING</Text>
            <Text style={styles.title}>Book your dream vacation</Text>
            <Text style={styles.copy}>
              Find comfortable hotels, compare locations, and send a booking request in minutes.
            </Text>

            <TouchableOpacity
              accessibilityRole="button"
              style={styles.primaryButton}
              onPress={() => navigation.navigate('SignUp')}
            >
              <Text style={styles.primaryButtonText}>Create an account</Text>
              <MaterialCommunityIcons name="arrow-right" color="#FFFFFF" size={20} />
            </TouchableOpacity>

            <TouchableOpacity
              accessibilityRole="button"
              style={styles.secondaryButton}
              onPress={() => navigation.navigate('LogIn')}
            >
              <Text style={styles.secondaryButtonText}>I already have an account</Text>
            </TouchableOpacity>

            <View style={styles.privacyRow}>
              <MaterialCommunityIcons name="shield-check-outline" color="#667085" size={17} />
              <Text style={styles.privacyText}>
                Your demo account is stored securely on this device.
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollContent: {
    flexGrow: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  shell: {
    width: '100%',
    maxWidth: 1100,
    overflow: 'hidden',
    borderRadius: 28,
    backgroundColor: '#F5FAFB',
  },
  wideShell: {
    flexDirection: 'row',
    alignItems: 'stretch',
  },
  imageContainer: {
    position: 'relative',
    width: '100%',
    minHeight: 280,
  },
  wideImageContainer: {
    flex: 1.2,
    width: undefined,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  imageBadge: {
    position: 'absolute',
    left: 18,
    bottom: 18,
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 999,
    backgroundColor: 'rgba(16, 42, 48, 0.82)',
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  imageBadgeText: {
    color: '#FFFFFF',
    fontWeight: '600',
    marginLeft: 7,
  },
  body: {
    padding: 26,
  },
  wideBody: {
    flex: 0.8,
    justifyContent: 'center',
    paddingHorizontal: 44,
  },
  brand: {
    width: 58,
    height: 58,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 18,
    backgroundColor: '#E1F3F6',
    marginBottom: 20,
  },
  eyebrow: {
    color: '#27899A',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1.8,
  },
  title: {
    color: '#1D2939',
    fontSize: 32,
    lineHeight: 39,
    fontWeight: '800',
    marginTop: 8,
  },
  copy: {
    color: '#667085',
    fontSize: 16,
    lineHeight: 24,
    marginTop: 12,
    marginBottom: 26,
  },
  primaryButton: {
    minHeight: 54,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 11,
    backgroundColor: '#27899A',
    paddingHorizontal: 18,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    marginRight: 9,
  },
  secondaryButton: {
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#B8C8CB',
    borderRadius: 11,
    marginTop: 12,
    paddingHorizontal: 18,
  },
  secondaryButtonText: {
    color: '#344054',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
  privacyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 22,
  },
  privacyText: {
    flex: 1,
    color: '#667085',
    fontSize: 12,
    lineHeight: 17,
    marginLeft: 7,
  },
});

export default Welcome;
