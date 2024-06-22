import { retrievedClustersList, requestedMoreCLusters } from "../features/clusterlist/slice";
import { doRetryOnTokenExpiration } from "../authSlice";
import { apiUrl } from "../const";

const doLoadMoreClusters = (): AppThunk => async (dispatch, getState) => {
  dispatch(requestedMoreCLusters());
  const requestedFilter = getState().clusters.requestedFilter;
  const result = await doRetryOnTokenExpiration({
    method: "get",
    url: `${apiUrl}/clusters?${requestedFilter}`,
  }, dispatch, getState);
  dispatch(retrievedClustersList({ requestedFilter, clusters: result.data,
                                   strat: "append" }));
};

export default doLoadMoreClusters;
