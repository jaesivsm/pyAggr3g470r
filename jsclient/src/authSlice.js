import axios from "axios";
import { createSlice } from "@reduxjs/toolkit";
import { apiUrl } from "./const";
import { storageGet, storageSet, storageRemove } from "./storageUtils";
import { authError } from "./features/noauth/noAuthSlice";

const authSlice = createSlice({
  name: "auth",
  initialState: { accessToken: null,
                  accessTokenExpiresAt: null,
                  refreshToken: storageGet("refreshToken", "local"),
  },
  reducers: {
    tokenAcquired: (state, action) => {
      const accessToken = action.payload["access_token"];
      const accessTokenExpiresAt = new Date(action.payload["access_token_expires_at"]).getTime();
      const refreshToken = action.payload["refresh_token"];
      if (refreshToken) {
        storageSet("refreshToken", refreshToken, "local");
        return { ...state, accessToken, refreshToken, accessTokenExpiresAt };
      } else {
        return { ...state, accessToken, accessTokenExpiresAt };
      }
    },
    purgeCredentials: () => {
      storageRemove("refreshToken", "local");
      return { accessToken: null, refreshToken: null, accessTokenExpiresAt: null };
    },
  },
});

export const { tokenAcquired, purgeCredentials} = authSlice.actions;

export default authSlice.reducer;

export const doRetryOnTokenExpiration = async (payload, dispatch, getState) => {
  const now = new Date().getTime();
  const state = getState();
  if (!state.auth.accessTokenExpiresAt
      || state.auth.accessTokenExpiresAt <= now) {
    // token has expired, trying to refresh it
    try {
      const result = await axios({
        method: "post",
        url: `${apiUrl}/auth/refresh`,
        headers: { "Authorization": state.auth.refreshToken }
      });
      dispatch(tokenAcquired(result.data));
      payload.headers = { "Authorization": result.data["access_token"] };
    } catch (err) { // failed to refresh it, logging out
      dispatch(purgeCredentials());
      dispatch(authError({ statusText: "EXPIRED" }));
      throw err;
    }
  } else {
    payload.headers = { "Authorization": state.auth.accessToken };
  }
  try {
    return await axios(payload);
  } catch (err) {
    // token seems to have expired
    if (err.response && err.response.status === 401
        && err.response.data && err.response.data.message
        && err.response.data.message === "Invalid token, Signature has expired") {
      dispatch(purgeCredentials());
      dispatch(authError({ statusText: "EXPIRED" }));
    } else {
      return err.response;
    }
  }
};
