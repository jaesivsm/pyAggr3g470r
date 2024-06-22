import qs from "qs";
import { apiUrl } from "../const";
import { doRetryOnTokenExpiration } from "../authSlice";
import { loadedUnreadCounts } from "../features/feedlist/slice";

const doMarkAllAsRead = (onlySingles): AppThunk => async (dispatch, getState) => {
  const params = { ...getState().clusters.filters };
  if(params.hasOwnProperty("from_date")) {
    delete params["from_date"];
  }
  if(onlySingles) {
    params["only_singles"] = true;
  }
  const stringifiedParams = qs.stringify(params);
  const result = await doRetryOnTokenExpiration({
    method: "put",
    url: `${apiUrl}/mark-all-as-read?${stringifiedParams}`,
  }, dispatch, getState);
  dispatch(loadedUnreadCounts({ unreads: result.data }));
};

export default doMarkAllAsRead;
