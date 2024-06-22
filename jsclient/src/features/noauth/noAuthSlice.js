import axios from "axios";
import { createSlice } from "@reduxjs/toolkit";
import { apiUrl } from "../../const";
import { tokenAcquired, purgeCredentials } from "../../authSlice";

const INITIAL_STATE = { loading: false,
                        loginError: null,
                        passwordError: null,
                        creationError: null,
                        recovery: null,
};

const noAuthSlice = createSlice({
  name: "noauth",
  initialState: { ...INITIAL_STATE },
  reducers: {
    requestSent: (state, action) => ({ ...state, loading: true }),
    responseRecieved: (state, action) => ({ ...INITIAL_STATE, ...action.payload }),
    authError: (state, action) => {
      state = { ...INITIAL_STATE };
      if (action.payload.statusText === "CONFLICT") {
        state.creationError = "Already in use. Please choose another login.";
      } else if (action.payload.statusText === "FORBIDDEN") {
        state.passwordError = "Wrong password.";
      } else if (action.payload.statusText === "NOT FOUND") {
        state.loginError = "User does not exist.";
      } else if (action.payload.statusText === "EXPIRED") {
        state.loginError = "Your session has expired, please log in again";
      } else {
        state.loginError = "Unknown error.";
        state.creationError = "Unknown error.";
      }
      return state;
    },
    alreadyExistingUser: (state, action) => ({ ...state, loading: false }),
  }
});

export const { requestSent, responseRecieved,
               alreadyExistingUser, authError,
} = noAuthSlice.actions;

export default noAuthSlice.reducer;

export const doLogin = (
  token: string,
  login: string,
  password: string
): AppThunk => async (dispatch) => {
  dispatch(requestSent());

  try {
    var result;
    if (!!token) {
      result = await axios({
        method: "post",
        url: `${apiUrl}/auth/refresh`,
        headers: { "Authorization": token }
      });
    } else {
      result = await axios.post(
        `${apiUrl}/auth`,
        { login, password },
        { responseType: "json" },
      );
    }
    dispatch(responseRecieved());
    dispatch(tokenAcquired(result.data));
  } catch (err) {
    dispatch(purgeCredentials());
    dispatch(authError(err.response));
  }
};

export const doSignUp = (
  login: string,
  password: string,
  email: string,
): AppThunk => async (dispatch) => {
  dispatch(requestSent());
  try {
    await axios({
      method: "post",
      url: `${apiUrl}/user`,
      data: { login, password, email },
    });
    dispatch(responseRecieved());
  } catch (err) {
    dispatch(authError(err.response));
  }
};

export const doInitRecovery = (
  login: string,
  email: string,
): AppThunk => async (dispatch) => {
  dispatch(requestSent());
  try {
    const result = await axios({
      method: "post",
      url: `${apiUrl}/auth/recovery`,
      data: { login, email },
    });
    dispatch(responseRecieved({ recovery: result }));
  } catch (err) {
    dispatch(responseRecieved({ recovery: err.response }));
  }
};

export const doRecovery = (
  login: string,
  email: string,
  token: string,
  password: string
): AppThunk => async (dispatch) => {
  dispatch(requestSent());
  try {
    await axios({
      method: "put",
      url: `${apiUrl}/auth/recovery`,
      data: { login, email, token, password },
    });
    dispatch(responseRecieved());
  } catch (err) {
    dispatch(responseRecieved({ recovery: err.response }));
  }
};

export const doValidOAuth = (code): AppThunk => async (dispatch) => {
  try {
    dispatch(requestSent());
    const result = await axios({
      method: "post",
      url: `${apiUrl}/oauth/callback/google`,
      data: { code },
    });
    dispatch(responseRecieved());
    dispatch(tokenAcquired(result.data));
  } catch (err) {
    dispatch(purgeCredentials());
    dispatch(authError(err.response));
  }
};
