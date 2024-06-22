import { apiUrl } from "../const";
import { doRetryOnTokenExpiration } from "../authSlice";
import doFetchFeeds from "./doFetchFeeds";

const doEditObj = (objType): AppThunk => async (dispatch, getState) => {
  const editState = getState().edit;
  const data = {};
  editState.editedKeys.forEach((key) => {
    data[key] = editState.loadedObj[key];
  });
  await doRetryOnTokenExpiration({
    method: "put",
    url: `${apiUrl}/${objType}${editState.loadedObj.id ? `/${editState.loadedObj.id}` : ""}`,
    data,
  }, dispatch, getState);
  dispatch(doFetchFeeds());
};

export default doEditObj;
