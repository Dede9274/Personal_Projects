import {Platform} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import Storage from 'expo-sqlite/kv-store';

const SESSION_KEY = 'hotel-booking.user-id';

export const readSessionUserId = async () => {
  const value = Platform.OS === 'web'
    ? await Storage.getItem(SESSION_KEY)
    : await SecureStore.getItemAsync(SESSION_KEY);

  if (!value) {
    return null;
  }

  const userId = Number(value);
  return Number.isInteger(userId) && userId > 0 ? userId : null;
};

export const saveSessionUserId = async (userId) => {
  const value = String(userId);

  if (Platform.OS === 'web') {
    await Storage.setItem(SESSION_KEY, value);
    return;
  }

  await SecureStore.setItemAsync(SESSION_KEY, value);
};

export const clearSession = async () => {
  if (Platform.OS === 'web') {
    await Storage.removeItem(SESSION_KEY);
    return;
  }

  await SecureStore.deleteItemAsync(SESSION_KEY);
};
