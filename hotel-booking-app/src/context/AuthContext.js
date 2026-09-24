import React, {createContext, useCallback, useContext, useEffect, useMemo, useState} from 'react';
import {useSQLiteContext} from 'expo-sqlite';
import {clearSession, readSessionUserId, saveSessionUserId} from '../services/session';
import {
  createPasswordSalt,
  derivePasswordHash,
  hashesMatch,
} from '../services/passwords';
import {normalizeEmail} from '../utils/auth';

const AuthContext = createContext(null);

const publicUser = (row) => ({
  id: row.id,
  firstName: row.first_name,
  lastName: row.last_name,
  email: row.email,
  createdAt: row.created_at,
});

export const AuthProvider = ({children}) => {
  const database = useSQLiteContext();
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const restoreSession = async () => {
      try {
        const userId = await readSessionUserId();

        if (!userId) {
          return;
        }

        const row = await database.getFirstAsync(
          `SELECT id, first_name, last_name, email, created_at
           FROM users
           WHERE id = ?`,
          userId
        );

        if (row && isMounted) {
          setUser(publicUser(row));
        } else if (!row) {
          await clearSession();
        }
      } catch {
        await clearSession().catch(() => {});
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    restoreSession();

    return () => {
      isMounted = false;
    };
  }, [database]);

  const signUp = useCallback(async ({firstName, lastName, email, password}) => {
    const normalizedEmail = normalizeEmail(email);
    const existingUser = await database.getFirstAsync(
      'SELECT id FROM users WHERE email = ?',
      normalizedEmail
    );

    if (existingUser) {
      throw new Error('An account with that email already exists.');
    }

    const salt = await createPasswordSalt();
    const passwordHash = await derivePasswordHash(password, salt);
    const createdAt = new Date().toISOString();
    let result;

    try {
      result = await database.runAsync(
        `INSERT INTO users (
          first_name,
          last_name,
          email,
          password_hash,
          password_salt,
          created_at
        ) VALUES (?, ?, ?, ?, ?, ?)`,
        String(firstName).trim(),
        String(lastName).trim(),
        normalizedEmail,
        passwordHash,
        salt,
        createdAt
      );
    } catch (error) {
      if (String(error?.message).includes('UNIQUE')) {
        throw new Error('An account with that email already exists.');
      }

      throw new Error('Your account could not be created. Please try again.');
    }

    const nextUser = {
      id: result.lastInsertRowId,
      firstName: String(firstName).trim(),
      lastName: String(lastName).trim(),
      email: normalizedEmail,
      createdAt,
    };

    await saveSessionUserId(nextUser.id).catch(() => {});
    setUser(nextUser);
    return nextUser;
  }, [database]);

  const signIn = useCallback(async ({email, password}) => {
    const row = await database.getFirstAsync(
      'SELECT * FROM users WHERE email = ?',
      normalizeEmail(email)
    );

    if (!row) {
      throw new Error('The email or password is incorrect.');
    }

    const candidateHash = await derivePasswordHash(password, row.password_salt);

    if (!hashesMatch(candidateHash, row.password_hash)) {
      throw new Error('The email or password is incorrect.');
    }

    const nextUser = publicUser(row);
    await saveSessionUserId(nextUser.id).catch(() => {});
    setUser(nextUser);
    return nextUser;
  }, [database]);

  const signOut = useCallback(async () => {
    try {
      await clearSession();
    } finally {
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({user, isLoading, signUp, signIn, signOut}),
    [user, isLoading, signUp, signIn, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider.');
  }

  return context;
};
