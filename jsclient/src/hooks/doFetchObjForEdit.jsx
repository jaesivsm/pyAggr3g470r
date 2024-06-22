import { openPanel, loadedObjToEdit, } from "../features/editpanel/slice";
import { doRetryOnTokenExpiration } from "../authSlice";
import { apiUrl } from "../const";

const doFetchObjForEdit = (type, id): AppThunk => async (dispatch, getState) => {
  dispatch(openPanel({ job: "load", objId: id, objType: type, isLoading: true }));
  const url = `${apiUrl}/${type}${id ? `/${id}` : ""}`;
  const result = await doRetryOnTokenExpiration({
    method: "get", url,
  }, dispatch, getState);
  dispatch(loadedObjToEdit({ data: result.data, job: "edit" }));
};

export default doFetchObjForEdit;
