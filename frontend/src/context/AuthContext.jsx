import {
createContext,
useContext,
useState,
useEffect,
useCallback,
} from 'react';

import api from '../api/axios';

const AuthContext = createContext(null);
const INACTIVITY_TIMEOUT_MS = 30 * 1000;

export const useAuth = () => {
const context = useContext(AuthContext);

if (!context) {
throw new Error(
'useAuth must be used within an AuthProvider'
);
}

return context;
};

export const AuthProvider = ({ children }) => {

const [user, setUser] = useState(null);
const [token, setToken] = useState(null);
const [loading, setLoading] = useState(true);

const logout = useCallback(() => {
setToken(null);
setUser(null);

localStorage.removeItem(
  'token'
);

localStorage.removeItem(
  'user'
);
}, []);

// Restore authentication after page refresh
useEffect(() => {

const storedToken =
  localStorage.getItem('token');

const storedUser =
  localStorage.getItem('user');


if (storedToken && storedUser) {

  try {

    setToken(storedToken);

    setUser(
      JSON.parse(storedUser)
    );

  } catch {

    // Remove corrupted data
    localStorage.removeItem('token');
    localStorage.removeItem('user');

  }

}

setLoading(false);

}, []);

// End authenticated sessions after 30 seconds without browser activity.
useEffect(() => {
if (!token) {
  return undefined;
}

let timeoutId;

const handleActivity = () => {
  window.clearTimeout(timeoutId);
  timeoutId = window.setTimeout(() => {
    logout();
    window.location.replace('/login');
  }, INACTIVITY_TIMEOUT_MS);
};

const activityEvents = [
  'mousedown',
  'mousemove',
  'keydown',
  'scroll',
  'touchstart',
  'pointerdown',
];

activityEvents.forEach((eventName) => {
  window.addEventListener(eventName, handleActivity, { passive: true });
});

handleActivity();

return () => {
  window.clearTimeout(timeoutId);
  activityEvents.forEach((eventName) => {
    window.removeEventListener(eventName, handleActivity);
  });
};
}, [token, logout]);

/**

LOGIN
Step 1:
Check email and password.
Backend sends OTP.
No JWT is stored yet.
*/
const login = async (
email,
password,
reactivate = false
) => {
const response =
  await api.post(
    '/auth/login',
    {
      email,
      password,
      reactivate,
    }
  );

// Response contains:
// { message, email, requiresVerification } OR { isDeactivated, ... }

return response.data;

};

/**

REGISTER
Step 1:
Create account.
Backend sends OTP.
No JWT is stored yet.
*/
const register = async (
username,
email,
password
) => {
const response =
  await api.post(
    '/auth/register',
    {
      username,
      email,
      password,
    }
  );

// Response contains:
// { message, email, requiresVerification }

return response.data;

};

/**

VERIFY OTP
Step 2:
Backend verifies OTP.
JWT token is received here.
*/
const verifyCode = async (
email,
code
) => {
const response =
  await api.post(
    '/auth/verify-code',
    {
      email,
      code,
    }
  );


const {
  token: newToken,
  user: userData,
} = response.data;


// Save authentication data
setToken(newToken);

setUser(userData);


localStorage.setItem(
  'token',
  newToken
);


localStorage.setItem(
  'user',
  JSON.stringify(userData)
);


return response.data;

};

/**

RESEND OTP
*/
const resendCode = async (
email
) => {
const response =
  await api.post(
    '/auth/resend-code',
    {
      email,
    }
  );

return response.data;

};

<<<<<<< Updated upstream
/**

LOGOUT
*/
const logout = () => {
setToken(null);
setUser(null);


localStorage.removeItem(
  'token'
);

localStorage.removeItem(
  'user'
);
};

/**
 * DEACTIVATE ACCOUNT
 * Temporarily pause account and immediately clear local session
 */
const deactivateAccount = async ({ duration, customDays, customDate, reason, password }) => {
  const response = await api.post('/auth/deactivate', {
    duration,
    customDays,
    customDate,
    reason,
    password,
  });

  logout();
  return response.data;
};

/**
 * REACTIVATE ACCOUNT
 * Explicitly request early account reactivation
 */
const reactivateAccount = async (email, password) => {
  const response = await api.post('/auth/reactivate', {
    email,
    password,
  });
  return response.data;
};

=======
>>>>>>> Stashed changes
const value = {

user,

token,

loading,

isAuthenticated: !!token,

isAdmin:
  user?.role === 'admin',


// Authentication functions
login,

register,

verifyCode,

resendCode,

logout,

deactivateAccount,

reactivateAccount,

};

return (

<AuthContext.Provider
  value={value}
>

  {children}

</AuthContext.Provider>

);

};

export default AuthContext;