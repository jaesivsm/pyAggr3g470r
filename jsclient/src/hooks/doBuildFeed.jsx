import qs from "qs";
import { apiUrl } from "../const";
import { doRetryOnTokenExpiration } from "../authSlice";
import { requestedBuildedFeed, loadedObjToEdit } from "../features/editpanel/slice";

const doBuildFeed = (url): AppThunk => async (dispatch, getState) => {
  dispatch(requestedBuildedFeed());
  const result = await doRetryOnTokenExpiration({
    method: "get",
    url: `${apiUrl}/feed/build?${qs.stringify({ url })}`,
  }, dispatch, getState);
  dispatch(loadedObjToEdit({ data: result.data, noIdCheck: true,
                             job: "build" }));
};

export default doBuildFeed;
