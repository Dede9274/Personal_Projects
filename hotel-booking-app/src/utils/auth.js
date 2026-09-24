const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const normalizeEmail = (email) => String(email || '').trim().toLowerCase();

export const validateSignIn = ({email, password}) => {
  const normalizedEmail = normalizeEmail(email);

  if (!normalizedEmail || !password) {
    return 'Enter your email address and password.';
  }

  if (!EMAIL_PATTERN.test(normalizedEmail)) {
    return 'Enter a valid email address.';
  }

  return null;
};

export const validateSignUp = ({
  firstName,
  lastName,
  email,
  password,
  confirmPassword,
}) => {
  if (!String(firstName).trim() || !String(lastName).trim()) {
    return 'Enter your first and last name.';
  }

  const signInError = validateSignIn({email, password});

  if (signInError) {
    return signInError;
  }

  if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    return 'Use at least 8 characters with a letter and a number.';
  }

  if (password !== confirmPassword) {
    return 'The passwords do not match.';
  }

  return null;
};
