import { configureStore, Action } from "@reduxjs/toolkit";
import { ThunkAction } from "redux-thunk";
import authReducer from "../authSlice";
import noAuthReducer from "../features/noauth/noAuthSlice";
import feedsReducer from "../features/feedlist/slice";
import clustersReducer from "../features/clusterlist/slice";
import editReducer from "../features/editpanel/slice";

export default configureStore({
  reducer: {
    auth: authReducer,
    noauth: noAuthReducer,
    feeds: feedsReducer,
    clusters: clustersReducer,
    edit: editReducer,
  },
});

export type AppThunk = ThunkAction<void, RootState, unknown, Action<string>>;
