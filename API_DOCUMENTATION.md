# Vauice Sports App - User Authentication API Documentation
## React Native with Expo Implementation Guide

## Base URL
```
http://127.0.0.1:8000/api/v1/  # Development
https://your-production-domain.com/api/v1/  # Production
```

## Authentication
Most endpoints use JWT (JSON Web Token) authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## Required Expo Packages
```bash
npx expo install @react-native-async-storage/async-storage
npx expo install expo-secure-store
```

---

## 1. User Registration 
**Endpoint:** `POST /user/register/`

**Description:** Register a new user (Talent or Mentor)

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "password2": "securepassword123",
  "firstname": "John",
  "lastname": "Doe",
  "gender": "male",
  "age": 25,
  "user_type": "talent",
  "phone_number": "+1234567890"
}
```

**Required Fields:**
- `username` (string): Unique username
- `email` (string): Valid email address
- `password` (string): Minimum 8 characters
- `password2` (string): Must match password
- `firstname` (string): User's first name
- `lastname` (string): User's last name
- `user_type` (string): Either "talent" or "mentor"

**Optional Fields:**
- `gender` (string): "male", "female", or "other"
- `age` (integer): User's age
- `phone_number` (string): Format: +999999999

**Success Response (201):**
```json
{
  "message": "User registered successfully!",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "gender": "male",
    "age": 25,
    "user_type": "talent",
    "phone_number": "+1234567890",
    "full_name": "John Doe",
    "is_superuser": false,
    "is_staff": false,
    "is_active": true,
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": null,
    "avatar_url": "defaults/avatar-default.png"
  },
  "otp": "1234567"
}
```

**Error Responses:**
- **400 Bad Request:** Validation errors
- **400 Bad Request:** Username/email already exists
- **400 Bad Request:** Passwords don't match
- **400 Bad Request:** Invalid user_type (admin not allowed)

---

## 2. User Login
**Endpoint:** `POST /user/token/`

**Description:** Authenticate user and get JWT tokens

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Success Response (200):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Responses:**
- **401 Unauthorized:** Invalid credentials

---

## 3. Token Refresh
**Endpoint:** `POST /user/token/refresh/`

**Description:** Get new access token using refresh token

**Authentication:** Not required

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Success Response (200):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Responses:**
- **401 Unauthorized:** Invalid or expired refresh token

---

## 4. User Logout
**Endpoint:** `POST /user/logout/`

**Description:** Logout user and clear refresh token

**Authentication:** Required (Bearer token)

**Request Body:** Empty

**Success Response (200):**
```json
{
  "message": "Logged out successfully!"
}
```

**Error Responses:**
- **400 Bad Request:** Logout failed
- **401 Unauthorized:** Invalid token

---

## 5. Get User Profile
**Endpoint:** `GET /user/profile/`

**Description:** Get current user's profile information

**Authentication:** Required (Bearer token)

**Request Body:** None

**Success Response (200):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "firstname": "John",
  "lastname": "Doe",
  "gender": "male",
  "age": 25,
  "user_type": "talent",
  "phone_number": "+1234567890",
  "full_name": "John Doe",
  "is_superuser": false,
  "is_staff": false,
  "is_active": true,
  "date_joined": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T10:30:00Z",
  "avatar_url": "defaults/avatar-default.png"
}
```

**Error Responses:**
- **401 Unauthorized:** Invalid token

---

## 6. Change Password (Authenticated)
**Endpoint:** `POST /user/change-password/`

**Description:** Change password for authenticated user

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "old_password": "currentpassword123",
  "new_password": "newpassword123",
  "new_password2": "newpassword123"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully!"
}
```

**Error Responses:**
- **400 Bad Request:** Old password incorrect
- **400 Bad Request:** New passwords don't match
- **400 Bad Request:** Invalid password format
- **401 Unauthorized:** Invalid token

---

## 7. Request Password Reset
**Endpoint:** `GET /user/password-reset/{email}/`

**Description:** Request password reset OTP via email

**Authentication:** Not required

**URL Parameters:**
- `email` (string): User's email address

**Request Body:** None

**Success Response (200):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "firstname": "John",
  "lastname": "Doe",
  "gender": "male",
  "age": 25,
  "user_type": "talent",
  "phone_number": "+1234567890",
  "full_name": "John Doe",
  "is_superuser": false,
  "is_staff": false,
  "is_active": true,
  "date_joined": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T10:30:00Z",
  "avatar_url": "defaults/avatar-default.png"
}
```

**Notes:**
- OTP is sent to the user's email
- OTP is printed to console for development (check server logs)
- User object is returned if email exists

**Error Responses:**
- **404 Not Found:** Email doesn't exist

---

## 8. Reset Password with OTP
**Endpoint:** `POST /user/password-change/`

**Description:** Reset password using OTP received via email

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "john@example.com",
  "otp": "1234567",
  "password": "newpassword123"
}
```

**Success Response (201):**
```json
{
  "message": "Password Changed Successfully"
}
```

**Error Responses:**
- **400 Bad Request:** Missing required fields
- **404 Not Found:** Invalid OTP or user doesn't exist

---

## 9. Check Username Availability
**Endpoint:** `POST /user/check-username/`

**Description:** Check if username is available for registration

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "johndoe"
}
```

**Success Response (200):**
```json
{
  "username": "johndoe",
  "available": false,
  "message": "Username already exists"
}
```

**Available Username Response:**
```json
{
  "username": "newuser123",
  "available": true,
  "message": "Username is available"
}
```

**Error Responses:**
- **400 Bad Request:** Username field is required

---

## 10. Check Email Availability
**Endpoint:** `POST /user/check-email/`

**Description:** Check if email is available for registration

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Success Response (200):**
```json
{
  "email": "john@example.com",
  "available": false,
  "message": "Email already exists"
}
```

**Available Email Response:**
```json
{
  "email": "newuser@example.com",
  "available": true,
  "message": "Email is available"
}
```

**Error Responses:**
- **400 Bad Request:** Email field is required
- **400 Bad Request:** Invalid email format

---

## React Native with Expo Integration Guide

### 1. Token Management (Secure Storage)
```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';

// Store tokens securely (prefer SecureStore for sensitive data)
const storeTokens = async (accessToken, refreshToken) => {
  try {
    // Store access token in SecureStore (more secure)
    await SecureStore.setItemAsync('access_token', accessToken);
    // Store refresh token in SecureStore
    await SecureStore.setItemAsync('refresh_token', refreshToken);
    
    // Also store in AsyncStorage for quick access (optional)
    await AsyncStorage.setItem('access_token', accessToken);
    await AsyncStorage.setItem('refresh_token', refreshToken);
  } catch (error) {
    console.error('Error storing tokens:', error);
  }
};

// Get stored tokens
const getTokens = async () => {
  try {
    const accessToken = await SecureStore.getItemAsync('access_token');
    const refreshToken = await SecureStore.getItemAsync('refresh_token');
    
    return {
      access: accessToken,
      refresh: refreshToken
    };
  } catch (error) {
    console.error('Error getting tokens:', error);
    return { access: null, refresh: null };
  }
};

// Clear tokens on logout
const clearTokens = async () => {
  try {
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('refresh_token');
  } catch (error) {
    console.error('Error clearing tokens:', error);
  }
};
```

### 2. API Request Helper (React Native)
```javascript
const BASE_URL = 'http://127.0.0.1:8000/api/v1/'; // Change for production

const apiRequest = async (endpoint, options = {}) => {
  const tokens = await getTokens();
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(tokens.access && { 'Authorization': `Bearer ${tokens.access}` }),
      ...options.headers
    },
    ...options
  };

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, config);
    
    // Handle token refresh if access token expires
    if (response.status === 401 && tokens.refresh) {
      const refreshed = await refreshToken(tokens.refresh);
      if (refreshed) {
        // Retry original request with new token
        const newTokens = await getTokens();
        config.headers.Authorization = `Bearer ${newTokens.access}`;
        return await fetch(`${BASE_URL}${endpoint}`, config);
      }
    }
    
    return response;
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
};

// Token refresh function
const refreshToken = async (refreshToken) => {
  try {
    const response = await fetch(`${BASE_URL}user/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken })
    });

    if (response.ok) {
      const data = await response.json();
      await storeTokens(data.access, data.refresh);
      return true;
    }
    return false;
  } catch (error) {
    console.error('Token refresh failed:', error);
    return false;
  }
};
```

### 3. Registration Flow (React Native)
```javascript
const registerUser = async (userData) => {
  try {
    const response = await apiRequest('user/register/', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    
    if (response.ok) {
      const data = await response.json();
      // Store OTP for verification if needed
      // In production, OTP should be sent via email/SMS
      console.log('Registration successful:', data);
      return data;
    } else {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

// Example usage in React Native component
const handleRegistration = async () => {
  try {
    setLoading(true);
    const userData = {
      username: username,
      email: email,
      password: password,
      password2: confirmPassword,
      firstname: firstName,
      lastname: lastName,
      gender: selectedGender,
      age: parseInt(age),
      user_type: userType, // 'talent' or 'mentor'
      phone_number: phoneNumber
    };
    
    const result = await registerUser(userData);
    // Navigate to OTP verification or login screen
    navigation.navigate('OTPVerification', { email: email });
  } catch (error) {
    Alert.alert('Registration Failed', error.message);
  } finally {
    setLoading(false);
  }
};
```

### 4. Login Flow (React Native)
```javascript
const loginUser = async (email, password) => {
  try {
    const response = await apiRequest('user/token/', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
      const data = await response.json();
      await storeTokens(data.access, data.refresh);
      return data;
    } else {
      throw new Error('Invalid credentials');
    }
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

// Example usage in React Native component
const handleLogin = async () => {
  try {
    setLoading(true);
    const result = await loginUser(email, password);
    
    // Store user data in context or state management
    // Navigate to main app
    navigation.replace('MainApp');
  } catch (error) {
    Alert.alert('Login Failed', error.message);
  } finally {
    setLoading(false);
  }
};
```

### 5. Password Reset Flow (React Native)
```javascript
const requestPasswordReset = async (email) => {
  try {
    const response = await apiRequest(`user/password-reset/${email}/`, {
      method: 'GET'
    });
    
    if (response.ok) {
      // OTP sent to email, show OTP input screen
      return true;
    } else {
      throw new Error('Email not found');
    }
  } catch (error) {
    console.error('Password reset request error:', error);
    throw error;
  }
};

const resetPassword = async (email, otp, newPassword) => {
  try {
    const response = await apiRequest('user/password-change/', {
      method: 'POST',
      body: JSON.stringify({ email, otp, password: newPassword })
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      const error = await response.json();
      throw new Error(error.message || 'Password reset failed');
    }
  } catch (error) {
    console.error('Password reset error:', error);
    throw error;
  }
};

// Example usage in React Native component
const handlePasswordReset = async () => {
  try {
    setLoading(true);
    await requestPasswordReset(email);
    Alert.alert('Success', 'OTP sent to your email');
    navigation.navigate('OTPInput', { email: email });
  } catch (error) {
    Alert.alert('Error', error.message);
  } finally {
    setLoading(false);
  }
};

const handleOTPSubmit = async () => {
  try {
    setLoading(true);
    await resetPassword(email, otp, newPassword);
    Alert.alert('Success', 'Password reset successfully');
    navigation.navigate('Login');
  } catch (error) {
    Alert.alert('Error', error.message);
  } finally {
    setLoading(false);
  }
};
```

### 6. Form Validation (React Native)
```javascript
const validateRegistration = (data) => {
  const errors = {};
  
  if (!data.username || data.username.length < 3) {
    errors.username = 'Username must be at least 3 characters';
  }
  
  if (!data.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.email = 'Valid email is required';
  }
  
  if (!data.password || data.password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
  }
  
  if (data.password !== data.password2) {
    errors.password2 = 'Passwords must match';
  }
  
  if (!data.firstname) {
    errors.firstname = 'First name is required';
  }
  
  if (!data.lastname) {
    errors.lastname = 'Last name is required';
  }
  
  if (!['talent', 'mentor'].includes(data.user_type)) {
    errors.user_type = 'User type must be talent or mentor';
  }
  
  return errors;
};

// Example usage in React Native component
const [errors, setErrors] = useState({});

const validateForm = () => {
  const formData = {
    username,
    email,
    password,
    password2: confirmPassword,
    firstname: firstName,
    lastname: lastName,
    user_type: userType
  };
  
  const validationErrors = validateRegistration(formData);
  setErrors(validationErrors);
  
  return Object.keys(validationErrors).length === 0;
};

// Display errors in TextInput
<TextInput
  value={username}
  onChangeText={setUsername}
  placeholder="Username"
  style={[styles.input, errors.username && styles.inputError]}
/>
{errors.username && <Text style={styles.errorText}>{errors.username}</Text>}
```

## Error Handling

### Common Error Codes
- **400 Bad Request:** Validation errors, missing fields
- **401 Unauthorized:** Invalid or expired token
- **404 Not Found:** Resource not found
- **500 Internal Server Error:** Server error

### Error Response Format
```json
{
  "error": "Error message",
  "field_errors": {
    "username": ["Username already exists"],
    "email": ["Invalid email format"]
  }
}
```

## React Native Specific Features

### 7. User Profile Management
```javascript
const getUserProfile = async () => {
  try {
    const response = await apiRequest('user/profile/', {
      method: 'GET'
    });
    
    if (response.ok) {
      const userData = await response.json();
      return userData;
    } else {
      throw new Error('Failed to fetch profile');
    }
  } catch (error) {
    console.error('Profile fetch error:', error);
    throw error;
  }
};

const logoutUser = async () => {
  try {
    const response = await apiRequest('user/logout/', {
      method: 'POST'
    });
    
    if (response.ok) {
      await clearTokens();
      // Navigate to login screen
      navigation.replace('Login');
    }
  } catch (error) {
    console.error('Logout error:', error);
    // Still clear tokens and navigate to login
    await clearTokens();
    navigation.replace('Login');
  }
};
```

### 8. Real-time Username/Email Validation
```javascript
const checkUsernameAvailability = async (username) => {
  try {
    const response = await apiRequest('user/check-username/', {
      method: 'POST',
      body: JSON.stringify({ username })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.available;
    }
    return false;
  } catch (error) {
    console.error('Username check error:', error);
    return false;
  }
};

const checkEmailAvailability = async (email) => {
  try {
    const response = await apiRequest('user/check-email/', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.available;
    }
    return false;
  } catch (error) {
    console.error('Email check error:', error);
    return false;
  }
};

// Usage in TextInput with debouncing
const [usernameAvailable, setUsernameAvailable] = useState(null);
const [emailAvailable, setEmailAvailable] = useState(null);

useEffect(() => {
  const timeoutId = setTimeout(async () => {
    if (username.length >= 3) {
      const available = await checkUsernameAvailability(username);
      setUsernameAvailable(available);
    }
  }, 500);

  return () => clearTimeout(timeoutId);
}, [username]);
```

### 9. Context Provider for Authentication
```javascript
// AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import { getTokens, storeTokens, clearTokens } from './authUtils';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const tokens = await getTokens();
      if (tokens.access) {
        // Verify token by fetching user profile
        const userData = await getUserProfile();
        setUser(userData);
        setIsAuthenticated(true);
      }
    } catch (error) {
      await clearTokens();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email, password) => {
    const result = await loginUser(email, password);
    setUser(result);
    setIsAuthenticated(true);
    return result;
  };

  const logout = async () => {
    await logoutUser();
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated,
      login,
      logout,
      checkAuthStatus
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
```

## Security Notes (React Native Specific)

1. **Token Storage:** Use `expo-secure-store` for sensitive data (tokens)
2. **AsyncStorage:** Use for non-sensitive data only
3. **Network Security:** Always use HTTPS in production
4. **Input Validation:** Validate all inputs before sending to API
5. **Error Handling:** Don't expose sensitive information in error messages
6. **Token Refresh:** Implement automatic token refresh with proper error handling
7. **App State:** Clear tokens when app goes to background (optional security measure)
8. **Biometric Auth:** Consider adding biometric authentication for extra security
9. **Certificate Pinning:** Implement certificate pinning for production apps
10. **Code Obfuscation:** Use ProGuard or similar for release builds

## Testing (React Native)

### Development Testing
- Use Swagger UI at `http://127.0.0.1:8000/`
- Check server logs for OTP codes during password reset testing
- Test all error scenarios with invalid data
- Use React Native Debugger for network inspection
- Test on both iOS and Android simulators/devices

### React Native Testing Tools
```bash
# Install testing dependencies
npm install --save-dev @testing-library/react-native @testing-library/jest-native

# Run tests
npm test

# Test specific file
npm test -- --testNamePattern="Login"
```

### Example Test for Login
```javascript
// Login.test.js
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import LoginScreen from '../LoginScreen';

test('login with valid credentials', async () => {
  const { getByPlaceholderText, getByText } = render(<LoginScreen />);
  
  const emailInput = getByPlaceholderText('Email');
  const passwordInput = getByPlaceholderText('Password');
  const loginButton = getByText('Login');
  
  fireEvent.changeText(emailInput, 'test@example.com');
  fireEvent.changeText(passwordInput, 'password123');
  fireEvent.press(loginButton);
  
  await waitFor(() => {
    expect(getByText('Login successful')).toBeTruthy();
  });
});
```

### Production Considerations
- Implement proper error logging with crash reporting (Sentry, Bugsnag)
- Add rate limiting for sensitive endpoints
- Monitor API usage and performance
- Set up proper email service for password reset
- Implement proper CORS configuration
- Use environment variables for API URLs
- Implement offline handling and retry logic
- Add analytics for user behavior tracking
- Implement proper app signing and distribution
- Set up CI/CD pipeline for automated testing and deployment

### Environment Configuration
```javascript
// config.js
const ENV = {
  development: {
    API_URL: 'http://127.0.0.1:8000/api/v1/',
    SENTRY_DSN: null,
  },
  staging: {
    API_URL: 'https://staging-api.vauice.com/api/v1/',
    SENTRY_DSN: 'your-sentry-dsn',
  },
  production: {
    API_URL: 'https://api.vauice.com/api/v1/',
    SENTRY_DSN: 'your-sentry-dsn',
  },
};

export default ENV[__DEV__ ? 'development' : 'production'];
``` 