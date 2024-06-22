import { requestedUnreadCounts, loadedUnreadCounts } from "../features/feedlist/slice";
import { doRetryOnTokenExpiration } from "../authSlice";
import { apiUrl } from "../const";

const doFetchUnreadCount = (): AppThunk => async (dispatch, getState) => {
  dispatch(requestedUnreadCounts());
  const result = await doRetryOnTokenExpiration({
    method: "get",
    url: `${apiUrl}/unreads`,
  }, dispatch, getState);
  dispatch(loadedUnreadCounts({ unreads: result.data }));
};

export default doFetchUnreadCount;
